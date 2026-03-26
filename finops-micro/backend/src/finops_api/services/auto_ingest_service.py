from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from threading import Lock
from typing import ClassVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.models.ingest_job import IngestJob
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.services.currency_rate_sync_service import CurrencyRateSyncService
from finops_api.services.ingest_service import run_ingest_job
from finops_api.services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class AutoIngestService:
    _attempt_lock: ClassVar[Lock] = Lock()
    _recent_attempts: ClassVar[dict[tuple[str, str, date], datetime]] = {}
    _attempt_cooldown: ClassVar[timedelta] = timedelta(minutes=10)

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
                current_tenant_key = tenant.tenant_key if tenant else (resolved_tenant_key or "default")
                tenant_id = tenant.tenant_id if tenant else None
                sync_window = self._resolve_sync_window(
                    provider=provider,
                    fallback_start=start,
                    sync_end=effective_end,
                    tenant_id=tenant_id,
                )
                if sync_window is None:
                    continue
                sync_start, sync_end = sync_window
                if self._has_recent_attempt(
                    provider,
                    current_tenant_key,
                    sync_end,
                    datetime.now(timezone.utc),
                ):
                    logger.info(
                        "Auto ingest incremental ignorado para %s/%s ate %s: tentativa recente em memoria.",
                        provider,
                        current_tenant_key,
                        sync_end.isoformat(),
                    )
                    continue
                try:
                    attempt_time = datetime.now(timezone.utc)
                    self._mark_recent_attempt(
                        provider,
                        current_tenant_key,
                        sync_end,
                        attempt_time,
                    )
                    result = run_ingest_job(
                        self.db,
                        provider=provider,
                        start=sync_start,
                        end=sync_end,
                        tenant_key=resolved_tenant_key,
                    )
                    logger.info(
                        "Auto ingest incremental executado para %s/%s (%s..%s @ %s): recebido=%s gravado=%s",
                        provider,
                        result.get("tenant_key"),
                        sync_start.isoformat(),
                        sync_end.isoformat(),
                        attempt_time.isoformat(timespec="seconds"),
                        result.get("rows_received"),
                        result.get("rows_written"),
                    )
                except Exception as exc:  # noqa: BLE001
                    self.db.rollback()
                    self._mark_recent_attempt(
                        provider,
                        current_tenant_key,
                        sync_end,
                        datetime.now(timezone.utc),
                    )
                    logger.warning("Auto ingest falhou para %s/%s: %s", provider, current_tenant_key, exc)
        self._ensure_currency_rate(end)

    def _ensure_currency_rate(self, as_of: date) -> None:
        try:
            CurrencyRateSyncService(self.db).ensure_brl_usd_rate(as_of)
        except Exception as exc:  # noqa: BLE001
            self.db.rollback()
            logger.warning("Sincronizacao de cotacao falhou para %s: %s", as_of.isoformat(), exc)

    @staticmethod
    def _effective_end(requested_end: date) -> date:
        return min(requested_end, date.today())

    @staticmethod
    def _tenant_keys_for_provider(tenant_service: TenantService, provider: str, requested_tenant_key: str | None) -> list[str | None]:
        if requested_tenant_key:
            return [requested_tenant_key]

        runtime_configs = tenant_service.get_runtime_configs(provider)
        if runtime_configs:
            return [config.tenant_key for config in runtime_configs]
        return [None]

    def _resolve_sync_window(
        self,
        provider: str,
        fallback_start: date,
        sync_end: date,
        tenant_id: UUID | None = None,
    ) -> tuple[date, date] | None:
        if sync_end < fallback_start:
            return None

        latest_ingested_date = self._latest_ingested_date(provider=provider, tenant_id=tenant_id)
        latest_available_date = self.repo.latest_usage_date(cloud=provider, tenant_id=tenant_id)
        sync_start = latest_ingested_date or latest_available_date or fallback_start

        if sync_start > sync_end:
            return None
        return sync_start, sync_end

    def _latest_ingested_date(self, provider: str, tenant_id: UUID | None = None) -> date | None:
        stmt = (
            select(func.max(IngestJob.source_window_end))
            .where(IngestJob.cloud == provider)
            .where(IngestJob.status == "success")
        )
        if tenant_id is not None:
            stmt = stmt.where(IngestJob.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar_one()

    @classmethod
    def _attempt_cache_key(
        cls,
        provider: str,
        tenant_key: str,
        end: date,
    ) -> tuple[str, str, date]:
        return provider, tenant_key, end

    @classmethod
    def _has_recent_attempt(
        cls,
        provider: str,
        tenant_key: str,
        end: date,
        now: datetime,
    ) -> bool:
        key = cls._attempt_cache_key(provider, tenant_key, end)
        with cls._attempt_lock:
            cls._cleanup_expired_attempts(now)
            last_attempt = cls._recent_attempts.get(key)
            if last_attempt is None:
                return False
            return (now - last_attempt) < cls._attempt_cooldown

    @classmethod
    def _mark_recent_attempt(
        cls,
        provider: str,
        tenant_key: str,
        end: date,
        now: datetime,
    ) -> None:
        key = cls._attempt_cache_key(provider, tenant_key, end)
        with cls._attempt_lock:
            cls._cleanup_expired_attempts(now)
            cls._recent_attempts[key] = now

    @classmethod
    def _cleanup_expired_attempts(cls, now: datetime) -> None:
        cutoff = now - cls._attempt_cooldown
        expired_keys = [key for key, attempted_at in cls._recent_attempts.items() if attempted_at < cutoff]
        for key in expired_keys:
            cls._recent_attempts.pop(key, None)
