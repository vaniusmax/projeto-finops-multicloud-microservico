from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.services.currency_rate_sync_service import CurrencyRateSyncService
from finops_api.services.ingest_service import run_ingest_job
from finops_api.services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class AutoIngestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FactCostRepository(db)

    def ensure_range(self, cloud: str, start: date, end: date, tenant_key: str | None = None) -> None:
        effective_end = self._effective_end(end)
        if effective_end < start:
            self._ensure_currency_rate(end)
            return

        if not settings.auto_ingest_on_request:
            self._ensure_currency_rate(end)
            return

        providers = ["aws", "azure", "oci"] if cloud == "all" else [cloud]
        tenant_service = TenantService(self.db)
        for provider in providers:
            tenant_keys = self._tenant_keys_for_provider(tenant_service, provider, tenant_key if provider == cloud else None)
            for resolved_tenant_key in tenant_keys:
                tenant = tenant_service.resolve_tenant(provider, resolved_tenant_key)
                tenant_id = tenant.tenant_id if tenant else None
                if provider == "aws":
                    has_service_data = self.repo.has_source_data_covering_range(
                        cloud="aws",
                        start=start,
                        end=effective_end,
                        source_ref="aws_ce_service_cli",
                        tenant_id=tenant_id,
                    )
                    has_account_data = self.repo.has_source_data_covering_range(
                        cloud="aws",
                        start=start,
                        end=effective_end,
                        source_ref="aws_ce_account_cli",
                        tenant_id=tenant_id,
                    )
                    has_data = has_service_data and has_account_data
                else:
                    has_data = self.repo.has_data_covering_range(provider, start, effective_end, tenant_id=tenant_id)
                if has_data:
                    continue
                try:
                    result = run_ingest_job(
                        self.db,
                        provider=provider,
                        start=start,
                        end=effective_end,
                        tenant_key=resolved_tenant_key,
                    )
                    logger.info(
                        "Auto ingest executado para %s/%s: recebido=%s gravado=%s",
                        provider,
                        result.get("tenant_key"),
                        result.get("rows_received"),
                        result.get("rows_written"),
                    )
                except Exception as exc:  # noqa: BLE001
                    self.db.rollback()
                    logger.warning("Auto ingest falhou para %s/%s: %s", provider, resolved_tenant_key or "default", exc)
        self._ensure_currency_rate(end)

    def _ensure_currency_rate(self, as_of: date) -> None:
        try:
            CurrencyRateSyncService(self.db).ensure_brl_usd_rate(as_of)
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            logger.warning("Sincronizacao de cotacao falhou para %s: %s", as_of.isoformat(), exc)

    @staticmethod
    def _effective_end(requested_end: date) -> date:
        today = date.today()
        if requested_end >= today:
            return today.fromordinal(today.toordinal() - 1)
        return requested_end

    @staticmethod
    def _tenant_keys_for_provider(tenant_service: TenantService, provider: str, requested_tenant_key: str | None) -> list[str | None]:
        if requested_tenant_key:
            return [requested_tenant_key]

        runtime_configs = tenant_service.get_runtime_configs(provider)
        if runtime_configs:
            return [config.tenant_key for config in runtime_configs]
        return [None]
