from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.services.ingest_service import run_ingest_job

logger = logging.getLogger(__name__)


class AutoIngestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FactCostRepository(db)

    def ensure_range(self, cloud: str, start: date, end: date) -> None:
        if not settings.auto_ingest_on_request:
            return

        providers = ["aws", "azure", "oci"] if cloud == "all" else [cloud]
        for provider in providers:
            has_data = self.repo.has_data_in_range(provider, start, end)
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
