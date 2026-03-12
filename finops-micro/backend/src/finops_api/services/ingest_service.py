from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.models.dim_tenant import DimTenant
from finops_api.models.dim_region import DimRegion
from finops_api.models.dim_scope import DimScope
from finops_api.models.dim_service import DimService
from finops_api.models.fact_cost_daily import FactCostDaily
from finops_api.models.fact_ingest_audit import FactIngestAudit
from finops_api.models.ingest_job import IngestJob
from finops_api.providers.aws.cli_client import AwsCliClient, AwsCliSettings
from finops_api.providers.azure.cli_client import AzureCliClient, AzureCliSettings
from finops_api.providers.common.types import CanonicalCostRow
from finops_api.providers.oci.cli_client import OciCliClient, OciCliSettings
from finops_api.services.tenant_service import TenantRuntimeConfig, TenantService

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    provider: str
    tenant_key: str
    rows_received: int
    rows_written: int
    rows_inserted: int = 0
    rows_updated: int = 0


class IngestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest_provider(self, provider: str, start: date, end: date, tenant_key: str | None = None) -> IngestResult:
        provider = provider.lower().strip()
        tenant_service = TenantService(self.db)
        tenant = tenant_service.resolve_tenant(provider, tenant_key)
        runtime_config = tenant_service.runtime_config_for(provider, tenant.tenant_key if tenant else tenant_key)
        if provider == "aws":
            rows = self._fetch_aws(start, end, runtime_config)
        elif provider == "azure":
            rows = self._fetch_azure(start, end, runtime_config)
        elif provider == "oci":
            rows = self._fetch_oci(start, end, runtime_config)
        else:
            raise ValueError(f"provider inválido: {provider}")

        if tenant is None:
            raise ValueError(f"tenant não resolvido para {provider}")

        written, rows_inserted, rows_updated = self._persist(rows, tenant)
        return IngestResult(
            provider=provider,
            tenant_key=tenant.tenant_key,
            rows_received=len(rows),
            rows_written=written,
            rows_inserted=rows_inserted,
            rows_updated=rows_updated,
        )

    def _fetch_aws(self, start: date, end: date, runtime_config: TenantRuntimeConfig | None) -> list[CanonicalCostRow]:
        provider_settings = AwsCliSettings(
            cli_path=settings.aws_cli_path,
            profile=(runtime_config.profile if runtime_config else settings.aws_profile) or None,
        )
        return AwsCliClient(provider_settings).fetch_daily_costs(start, end)

    def _fetch_azure(self, start: date, end: date, runtime_config: TenantRuntimeConfig | None) -> list[CanonicalCostRow]:
        azure_mg = str((runtime_config.metadata.get("management_group_id") if runtime_config else None) or settings.azure_management_group_id or "")
        provider_settings = AzureCliSettings(
            management_group_id=azure_mg,
            api_version=settings.azure_api_version,
            cli_path=settings.azure_cli_path,
        )
        return AzureCliClient(provider_settings).fetch_daily_costs(start, end)

    def _fetch_oci(self, start: date, end: date, runtime_config: TenantRuntimeConfig | None) -> list[CanonicalCostRow]:
        oci_tenant = str((runtime_config.metadata.get("tenant_id") if runtime_config else None) or settings.oci_tenant_id or "")
        provider_settings = OciCliSettings(
            tenant_id=oci_tenant,
            cli_path=settings.oci_cli_path,
            profile=(runtime_config.profile if runtime_config else settings.oci_profile),
            region=settings.oci_region,
            compartment_depth=settings.oci_compartment_depth,
        )
        return OciCliClient(provider_settings).fetch_daily_costs(start, end)

    def _persist(self, rows: Iterable[CanonicalCostRow], tenant: DimTenant) -> tuple[int, int, int]:
        written = 0
        rows_inserted = 0
        rows_updated = 0
        scope_cache: dict[tuple[str, str, str], str] = {}
        service_cache: dict[tuple[str, str], str] = {}
        region_cache: dict[tuple[str, str], str] = {}

        normalized_rows = self._coalesce_rows(rows)
        for row in normalized_rows:
            self._cleanup_legacy_currency_mismatch(row, tenant)
            scope_id = self._get_or_create_scope(row, tenant, scope_cache)
            service_id = self._get_or_create_service(row, service_cache)
            region_id = self._get_or_create_region(row, region_cache)

            values = dict(
                usage_date=row.usage_date,
                cloud=row.cloud,
                tenant_id=tenant.tenant_id,
                scope_id=scope_id,
                service_id=service_id,
                region_id=region_id,
                scope_key=row.scope_key,
                service_key=row.service_key,
                region_key=row.region_key,
                currency_code=row.currency_code.upper(),
                amount=self._to_decimal(row.amount),
                amount_brl=self._to_decimal(row.amount_brl) if row.amount_brl is not None else None,
                source_ref=row.source_ref,
                source_record_id=None,
                tags={},
                metadata_json=row.metadata_json,
            )

            # O schema alvo usa índice único com expressões (COALESCE), não constraint nomeada.
            # Então usamos insert DO NOTHING e, em caso de conflito, fazemos UPDATE manual pela chave natural.
            insert_stmt = insert(FactCostDaily).values(**values).on_conflict_do_nothing()
            result = self.db.execute(insert_stmt)
            if int(result.rowcount or 0) == 0:
                update_stmt = (
                    update(FactCostDaily)
                    .where(FactCostDaily.usage_date == row.usage_date)
                    .where(FactCostDaily.cloud == row.cloud)
                    .where(FactCostDaily.tenant_id == tenant.tenant_id)
                    .where(FactCostDaily.scope_key == row.scope_key)
                    .where(FactCostDaily.service_key == row.service_key)
                    .where(func.coalesce(FactCostDaily.region_key, "") == (row.region_key or ""))
                    .where(func.coalesce(FactCostDaily.resource_id, "") == "")
                    .where(FactCostDaily.currency_code == row.currency_code.upper())
                    .where(func.coalesce(FactCostDaily.charge_type, "") == "")
                    .where(func.coalesce(FactCostDaily.pricing_model, "") == "")
                    .values(
                        tenant_id=tenant.tenant_id,
                        scope_id=scope_id,
                        service_id=service_id,
                        region_id=region_id,
                        amount=self._to_decimal(row.amount),
                        amount_brl=self._to_decimal(row.amount_brl) if row.amount_brl is not None else None,
                        metadata_json=row.metadata_json,
                        updated_at=datetime.now(timezone.utc),
                    )
                )
                self.db.execute(update_stmt)
                rows_updated += 1
            else:
                rows_inserted += 1
            written += 1

        self.db.commit()
        return written, rows_inserted, rows_updated

    def _coalesce_rows(self, rows: Iterable[CanonicalCostRow]) -> list[CanonicalCostRow]:
        aggregated: dict[tuple[str, date, str, str, str, str, str], CanonicalCostRow] = {}

        for row in rows:
            key = (
                row.cloud,
                row.usage_date,
                row.scope_key,
                row.service_key,
                row.region_key,
                row.currency_code.upper(),
                row.source_ref,
            )
            existing = aggregated.get(key)
            if existing is None:
                aggregated[key] = row
                continue

            aggregated[key] = CanonicalCostRow(
                cloud=row.cloud,
                usage_date=row.usage_date,
                scope_key=row.scope_key,
                scope_name=row.scope_name,
                service_key=row.service_key,
                service_name=row.service_name,
                region_key=row.region_key,
                region_name=row.region_name,
                currency_code=row.currency_code.upper(),
                amount=self._to_decimal(existing.amount) + self._to_decimal(row.amount),
                amount_brl=self._sum_nullable_decimals(existing.amount_brl, row.amount_brl),
                source_ref=row.source_ref,
                metadata_json=self._merge_metadata(existing.metadata_json, row.metadata_json),
            )

        return list(aggregated.values())

    def _cleanup_legacy_currency_mismatch(self, row: CanonicalCostRow, tenant: DimTenant) -> None:
        # Corrige legado: alguns registros Azure/OCI foram persistidos como USD
        # mesmo com valor já em BRL, inflando KPIs por conversão duplicada.
        if row.cloud not in {"azure", "oci"}:
            return
        if str(row.currency_code or "").upper() != "BRL":
            return

        stmt = (
            delete(FactCostDaily)
            .where(FactCostDaily.usage_date == row.usage_date)
            .where(FactCostDaily.cloud == row.cloud)
            .where(FactCostDaily.tenant_id == tenant.tenant_id)
            .where(FactCostDaily.scope_key == row.scope_key)
            .where(FactCostDaily.service_key == row.service_key)
            .where(func.coalesce(FactCostDaily.region_key, "") == (row.region_key or ""))
            .where(func.coalesce(FactCostDaily.resource_id, "") == "")
            .where(func.coalesce(FactCostDaily.charge_type, "") == "")
            .where(func.coalesce(FactCostDaily.pricing_model, "") == "")
            .where(FactCostDaily.source_ref == row.source_ref)
            .where(FactCostDaily.currency_code == "USD")
        )
        self.db.execute(stmt)

    def _get_or_create_scope(self, row: CanonicalCostRow, tenant: DimTenant, cache: dict[tuple[str, str, str], str]) -> str:
        key = (row.cloud, str(tenant.tenant_id), row.scope_key)
        cached = cache.get(key)
        if cached:
            return cached

        existing = self.db.execute(
            select(DimScope.scope_id).where(
                DimScope.cloud == row.cloud,
                DimScope.tenant_id == tenant.tenant_id,
                DimScope.scope_key == row.scope_key,
            )
        ).scalar_one_or_none()
        if existing:
            self.db.execute(
                update(DimScope)
                .where(DimScope.scope_id == existing)
                .values(scope_name=row.scope_name, metadata_json={"origin": "cli_ingest"})
            )
            cache[key] = str(existing)
            return str(existing)

        stmt = insert(DimScope).values(
            tenant_id=tenant.tenant_id,
            cloud=row.cloud,
            scope_key=row.scope_key,
            scope_name=row.scope_name,
            metadata_json={"origin": "cli_ingest"},
        ).on_conflict_do_update(
            index_elements=[DimScope.tenant_id, DimScope.scope_key],
            set_={
                DimScope.scope_name: row.scope_name,
                DimScope.metadata_json: {"origin": "cli_ingest"},
            },
        )
        self.db.execute(stmt)
        scope_id = self.db.execute(
            select(DimScope.scope_id).where(
                DimScope.cloud == row.cloud,
                DimScope.tenant_id == tenant.tenant_id,
                DimScope.scope_key == row.scope_key,
            )
        ).scalar_one()
        cache[key] = str(scope_id)
        return str(scope_id)

    def _get_or_create_service(self, row: CanonicalCostRow, cache: dict[tuple[str, str], str]) -> str:
        key = (row.cloud, row.service_key)
        cached = cache.get(key)
        if cached:
            return cached

        existing = self.db.execute(
            select(DimService.service_id).where(
                DimService.cloud == row.cloud,
                DimService.service_key == row.service_key,
            )
        ).scalar_one_or_none()
        if existing:
            cache[key] = str(existing)
            return str(existing)

        stmt = insert(DimService).values(
            cloud=row.cloud,
            service_key=row.service_key,
            service_name=row.service_name,
            metadata_json={"origin": "cli_ingest"},
        ).on_conflict_do_nothing(index_elements=[DimService.cloud, DimService.service_key])
        self.db.execute(stmt)
        service_id = self.db.execute(
            select(DimService.service_id).where(
                DimService.cloud == row.cloud,
                DimService.service_key == row.service_key,
            )
        ).scalar_one()
        cache[key] = str(service_id)
        return str(service_id)

    def _get_or_create_region(self, row: CanonicalCostRow, cache: dict[tuple[str, str], str]) -> str:
        key = (row.cloud, row.region_key)
        cached = cache.get(key)
        if cached:
            return cached

        existing = self.db.execute(
            select(DimRegion.region_id).where(DimRegion.cloud == row.cloud, DimRegion.region_key == row.region_key)
        ).scalar_one_or_none()
        if existing:
            cache[key] = str(existing)
            return str(existing)

        stmt = insert(DimRegion).values(
            cloud=row.cloud,
            region_key=row.region_key,
            region_name=row.region_name,
            metadata_json={"origin": "cli_ingest"},
        ).on_conflict_do_nothing(index_elements=[DimRegion.cloud, DimRegion.region_key])
        self.db.execute(stmt)
        region_id = self.db.execute(
            select(DimRegion.region_id).where(DimRegion.cloud == row.cloud, DimRegion.region_key == row.region_key)
        ).scalar_one()
        cache[key] = str(region_id)
        return str(region_id)

    @staticmethod
    def _to_decimal(value: Decimal | None) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    @staticmethod
    def _sum_nullable_decimals(left: Decimal | None, right: Decimal | None) -> Decimal | None:
        if left is None and right is None:
            return None
        return IngestService._to_decimal(left) + IngestService._to_decimal(right)

    @staticmethod
    def _merge_metadata(existing: dict[str, Any] | None, incoming: dict[str, Any] | None) -> dict[str, Any]:
        merged: dict[str, Any] = {**(existing or {}), **(incoming or {})}

        sku_names = sorted(
            {
                *IngestService._extract_metadata_strings(existing, "sku_name"),
                *IngestService._extract_metadata_strings(existing, "sku_names"),
                *IngestService._extract_metadata_strings(incoming, "sku_name"),
                *IngestService._extract_metadata_strings(incoming, "sku_names"),
            }
        )
        if len(sku_names) > 1:
            merged.pop("sku_name", None)
            merged["sku_names"] = sku_names
            merged["sku_count"] = len(sku_names)
        elif len(sku_names) == 1:
            merged["sku_name"] = sku_names[0]
            merged.pop("sku_names", None)
            merged.pop("sku_count", None)

        merged_records = int((existing or {}).get("merged_records") or 1) + int((incoming or {}).get("merged_records") or 1)
        if merged_records > 1:
            merged["merged_records"] = merged_records

        return merged

    @staticmethod
    def _extract_metadata_strings(payload: dict[str, Any] | None, key: str) -> set[str]:
        if not payload:
            return set()

        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return {value.strip()}
        if isinstance(value, list):
            return {str(item).strip() for item in value if str(item).strip()}
        return set()


def run_ingest_job(db: Session, provider: str, start: date, end: date, tenant_key: str | None = None) -> dict:
    provider_name = provider.lower().strip()
    tenant = TenantService(db).resolve_tenant(provider_name, tenant_key)
    if tenant is None:
        raise ValueError(f"tenant não resolvido para {provider_name}")
    started = datetime.now(timezone.utc)
    ingest_job = IngestJob(
        tenant_id=tenant.tenant_id,
        cloud=provider_name,
        status="running",
        started_at=started,
        source="provider_cli",
        source_window_start=start,
        source_window_end=end,
        details_json={"start": start.isoformat(), "end": end.isoformat(), "tenant_key": tenant.tenant_key},
    )
    db.add(ingest_job)
    db.commit()

    service = IngestService(db)
    try:
        result = service.ingest_provider(provider_name, start, end, tenant_key=tenant.tenant_key)
        ingest_job.status = "success"
        ingest_job.finished_at = datetime.now(timezone.utc)
        ingest_job.details_json = {
            **(ingest_job.details_json or {}),
            **asdict(result),
        }
        db.add(
            FactIngestAudit(
                job_id=ingest_job.job_id,
                tenant_id=tenant.tenant_id,
                cloud=provider_name,
                rows_inserted=result.rows_inserted,
                rows_updated=result.rows_updated,
                rows_deleted=0,
            )
        )
        db.commit()
        return asdict(result)
    except Exception as exc:  # noqa: BLE001
        # Limpa transacao quebrada (flush/execute anterior) antes de persistir status de erro.
        db.rollback()
        try:
            failed_job = db.get(IngestJob, ingest_job.job_id)
            if failed_job is not None:
                failed_job.status = "failed"
                failed_job.finished_at = datetime.now(timezone.utc)
                failed_job.error_message = str(exc)
                db.commit()
            else:
                logger.warning("Ingest job %s nao encontrado para marcar falha.", ingest_job.job_id)
        except Exception:  # noqa: BLE001
            db.rollback()
            logger.exception("Falha ao persistir status de erro do ingest job %s", ingest_job.job_id)
        raise
