from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.services.currency_rate_sync_service import CurrencyRateSyncService
from finops_api.services.ingest_service import run_ingest_job

logger = logging.getLogger(__name__)


class AutoIngestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FactCostRepository(db)

    def ensure_range(self, cloud: str, start: date, end: date) -> None:
        if not settings.auto_ingest_on_request:
            self._ensure_currency_rate(end)
            return

        providers = ["aws", "azure", "oci"] if cloud == "all" else [cloud]
        for provider in providers:
            if provider == "aws":
                has_service_data = self.repo.has_source_data_covering_range(
                    cloud="aws",
                    start=start,
                    end=end,
                    source_ref="aws_ce_service_cli",
                )
                has_account_data = self.repo.has_source_data_covering_range(
                    cloud="aws",
                    start=start,
                    end=end,
                    source_ref="aws_ce_account_cli",
                )
                has_data = has_service_data and has_account_data
            else:
                has_data = self.repo.has_data_covering_range(provider, start, end)
            if has_data:
                continue
            try:
                result = run_ingest_job(self.db, provider=provider, start=start, end=end)
                logger.info(
                    "Auto ingest executado para %s: recebido=%s gravado=%s",
                    provider,
                    result.get("rows_received"),
                    result.get("rows_written"),
                )
            except Exception as exc:  # noqa: BLE001
                # Garante sessao limpa para as proximas queries do request.
                self.db.rollback()
                logger.warning("Auto ingest falhou para %s: %s", provider, exc)
        self._ensure_currency_rate(end)

    def _ensure_currency_rate(self, as_of: date) -> None:
        try:
            CurrencyRateSyncService(self.db).ensure_brl_usd_rate(as_of)
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            logger.warning("Sincronizacao de cotacao falhou para %s: %s", as_of.isoformat(), exc)
