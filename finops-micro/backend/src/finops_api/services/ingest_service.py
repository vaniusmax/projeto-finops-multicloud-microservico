from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
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
    rows_deleted: int = 0


class IngestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest_provider(
        self,
        provider: str,
        start: date,
        end: date,
        tenant_key: str | None = None,
        job_id: UUID | None = None,
    ) -> IngestResult:
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

        written, rows_inserted, rows_deleted = self._persist(rows, tenant, job_id=job_id)
        return IngestResult(
            provider=provider,
            tenant_key=tenant.tenant_key,
            rows_received=len(rows),
            rows_written=written,
            rows_inserted=rows_inserted,
            rows_updated=0,
            rows_deleted=rows_deleted,
        )

    def _fetch_aws(self, start: date, end: date, runtime_config: TenantRuntimeConfig | None) -> list[CanonicalCostRow]:
        provider_settings = AwsCliSettings(
            cli_path=settings.aws_cli_path,
            profile=(runtime_config.profile if runtime_config else settings.aws_profile) or None,
            timeout=settings.cli_subprocess_timeout,
            retry_attempts=settings.cli_retry_attempts,
            retry_delay=settings.cli_retry_delay,
        )
        return AwsCliClient(provider_settings).fetch_daily_costs(start, end)

    def _fetch_azure(self, start: date, end: date, runtime_config: TenantRuntimeConfig | None) -> list[CanonicalCostRow]:
        azure_mg = str((runtime_config.metadata.get("management_group_id") if runtime_config else None) or settings.azure_management_group_id or "")
        provider_settings = AzureCliSettings(
            management_group_id=azure_mg,
            api_version=settings.azure_api_version,
            cli_path=settings.azure_cli_path,
            timeout=settings.cli_subprocess_timeout,
            retry_attempts=settings.cli_retry_attempts,
            retry_delay=settings.cli_retry_delay,
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
            timeout=settings.cli_subprocess_timeout,
            retry_attempts=settings.cli_retry_attempts,
            retry_delay=settings.cli_retry_delay,
        )
        return OciCliClient(provider_settings).fetch_daily_costs(start, end)

    # ------------------------------------------------------------------
    # Persist pipeline: DELETE existing range + bulk INSERT
    # ------------------------------------------------------------------

    def _persist(
        self,
        rows: Iterable[CanonicalCostRow],
        tenant: DimTenant,
        job_id: UUID | None = None,
    ) -> tuple[int, int, int]:
        normalized_rows = self._coalesce_rows(rows)
        if not normalized_rows:
            return 0, 0, 0

        scope_cache = self._bulk_ensure_scopes(normalized_rows, tenant)
        service_cache = self._bulk_ensure_services(normalized_rows)
        region_cache = self._bulk_ensure_regions(normalized_rows)

        min_date = min(r.usage_date for r in normalized_rows)
        max_date = max(r.usage_date for r in normalized_rows)
        source_refs = {r.source_ref for r in normalized_rows}
        clouds = {r.cloud for r in normalized_rows}

        rows_deleted = self._delete_existing_range(tenant, clouds, min_date, max_date, source_refs)

        all_values: list[dict[str, Any]] = []
        for row in normalized_rows:
            all_values.append(
                dict(
                    usage_date=row.usage_date,
                    cloud=row.cloud,
                    tenant_id=tenant.tenant_id,
                    scope_id=scope_cache.get((row.cloud, row.scope_key)),
                    service_id=service_cache.get((row.cloud, row.service_key)),
                    region_id=region_cache.get((row.cloud, row.region_key)),
                    job_id=job_id,
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
            )

        rows_inserted = 0
        batch_size = settings.ingest_batch_size
        for i in range(0, len(all_values), batch_size):
            batch = all_values[i : i + batch_size]
            stmt = insert(FactCostDaily).values(batch).on_conflict_do_nothing()
            result = self.db.execute(stmt)
            rows_inserted += result.rowcount or 0

        self.db.commit()
        return len(normalized_rows), rows_inserted, rows_deleted

    def _delete_existing_range(
        self,
        tenant: DimTenant,
        clouds: set[str],
        min_date: date,
        max_date: date,
        source_refs: set[str],
    ) -> int:
        stmt = (
            delete(FactCostDaily)
            .where(FactCostDaily.tenant_id == tenant.tenant_id)
            .where(FactCostDaily.cloud.in_(clouds))
            .where(FactCostDaily.usage_date.between(min_date, max_date))
            .where(FactCostDaily.source_ref.in_(source_refs))
        )
        return self.db.execute(stmt).rowcount or 0

    # ------------------------------------------------------------------
    # Bulk dimension resolution
    # ------------------------------------------------------------------

    def _bulk_ensure_scopes(
        self,
        rows: list[CanonicalCostRow],
        tenant: DimTenant,
    ) -> dict[tuple[str, str], str]:
        unique: dict[tuple[str, str], str] = {}
        for row in rows:
            unique.setdefault((row.cloud, row.scope_key), row.scope_name)

        if unique:
            values = [
                dict(
                    tenant_id=tenant.tenant_id,
                    cloud=cloud,
                    scope_key=scope_key,
                    scope_name=scope_name,
                    metadata_json={"origin": "cli_ingest"},
                )
                for (cloud, scope_key), scope_name in unique.items()
            ]
            insert_stmt = insert(DimScope).values(values)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=[DimScope.tenant_id, DimScope.scope_key],
                set_={
                    DimScope.scope_name: insert_stmt.excluded.scope_name,
                    DimScope.metadata_json: {"origin": "cli_ingest"},
                },
            )
            self.db.execute(upsert_stmt)

        existing = self.db.execute(
            select(DimScope.cloud, DimScope.scope_key, DimScope.scope_id)
            .where(DimScope.tenant_id == tenant.tenant_id)
        ).all()
        return {(str(r.cloud), str(r.scope_key)): str(r.scope_id) for r in existing}

    def _bulk_ensure_services(self, rows: list[CanonicalCostRow]) -> dict[tuple[str, str], str]:
        unique: dict[tuple[str, str], str] = {}
        for row in rows:
            unique.setdefault((row.cloud, row.service_key), row.service_name)

        if unique:
            values = [
                dict(
                    cloud=cloud,
                    service_key=service_key,
                    service_name=service_name,
                    metadata_json={"origin": "cli_ingest"},
                )
                for (cloud, service_key), service_name in unique.items()
            ]
            insert_stmt = insert(DimService).values(values)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=[DimService.cloud, DimService.service_key],
                set_={
                    DimService.service_name: insert_stmt.excluded.service_name,
                    DimService.metadata_json: {"origin": "cli_ingest"},
                },
            )
            self.db.execute(upsert_stmt)

        clouds = {r.cloud for r in rows}
        existing = self.db.execute(
            select(DimService.cloud, DimService.service_key, DimService.service_id)
            .where(DimService.cloud.in_(clouds))
        ).all()
        return {(str(r.cloud), str(r.service_key)): str(r.service_id) for r in existing}

    def _bulk_ensure_regions(self, rows: list[CanonicalCostRow]) -> dict[tuple[str, str], str]:
        unique: dict[tuple[str, str], str] = {}
        for row in rows:
            unique.setdefault((row.cloud, row.region_key), row.region_name)

        if unique:
            values = [
                dict(
                    cloud=cloud,
                    region_key=region_key,
                    region_name=region_name,
                    metadata_json={"origin": "cli_ingest"},
                )
                for (cloud, region_key), region_name in unique.items()
            ]
            insert_stmt = insert(DimRegion).values(values)
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=[DimRegion.cloud, DimRegion.region_key],
                set_={
                    DimRegion.region_name: insert_stmt.excluded.region_name,
                    DimRegion.metadata_json: {"origin": "cli_ingest"},
                },
            )
            self.db.execute(upsert_stmt)

        clouds = {r.cloud for r in rows}
        existing = self.db.execute(
            select(DimRegion.cloud, DimRegion.region_key, DimRegion.region_id)
            .where(DimRegion.cloud.in_(clouds))
        ).all()
        return {(str(r.cloud), str(r.region_key)): str(r.region_id) for r in existing}

    # ------------------------------------------------------------------
    # Row coalescing
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
        result = service.ingest_provider(
            provider_name,
            start,
            end,
            tenant_key=tenant.tenant_key,
            job_id=ingest_job.job_id,
        )
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
                rows_deleted=result.rows_deleted,
            )
        )
        db.commit()
        return asdict(result)
    except Exception as exc:  # noqa: BLE001
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
