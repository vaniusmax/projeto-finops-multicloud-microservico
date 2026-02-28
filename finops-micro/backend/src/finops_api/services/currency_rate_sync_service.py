from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.repositories.currency_rate_repo import CurrencyRateRepository

logger = logging.getLogger(__name__)


@dataclass
class CurrencyQuote:
    rate_date: date
    brl_per_usd: float
    source: str


class CurrencyRateSyncService:
    def __init__(
        self,
        db: Session,
        repo: CurrencyRateRepository | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.db = db
        self.repo = repo or CurrencyRateRepository(db)
        self._client = client

    def ensure_brl_usd_rate(self, as_of: date) -> float | None:
        if not settings.currency_rate_sync_on_request:
            return self.repo.get_brl_per_usd(as_of)

        existing = self.repo.get_exact_brl_per_usd(as_of)
        if existing is not None:
            return existing

        quote = self._fetch_quote(as_of)
        if quote is None:
            return self.repo.get_brl_per_usd(as_of)

        self.repo.upsert_rate(quote.rate_date, "USD", "BRL", quote.brl_per_usd)
        self.repo.upsert_rate(quote.rate_date, "BRL", "USD", 1.0 / quote.brl_per_usd)
        self.db.commit()
        logger.info(
            "Cotacao USD/BRL sincronizada para %s via %s: %.6f",
            quote.rate_date.isoformat(),
            quote.source,
            quote.brl_per_usd,
        )
        return quote.brl_per_usd

    def _fetch_quote(self, as_of: date) -> CurrencyQuote | None:
        try:
            response = self._get_client().get(settings.currency_rate_provider_url)
            response.raise_for_status()
            payload = response.json()
            return self._parse_quote(payload, requested_date=as_of)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao sincronizar cotacao USD/BRL: %s", exc)
            self.db.rollback()
            return None

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        self._client = httpx.Client(timeout=settings.currency_rate_timeout_seconds)
        return self._client

    @classmethod
    def _parse_quote(cls, payload: Any, requested_date: date) -> CurrencyQuote:
        if isinstance(payload, list) and payload:
            return cls._parse_quote(payload[0], requested_date)

        if not isinstance(payload, dict):
            raise ValueError("Payload de cotacao invalido")

        rate = cls._extract_rate(payload)
        quote_date = cls._extract_date(payload, requested_date)
        return CurrencyQuote(
            rate_date=quote_date,
            brl_per_usd=rate,
            source=str(payload.get("source") or payload.get("code") or payload.get("pair") or "api"),
        )

    @staticmethod
    def _extract_rate(payload: dict[str, Any]) -> float:
        direct_candidates = [
            payload.get("bid"),
            payload.get("ask"),
            payload.get("rate"),
            payload.get("value"),
            payload.get("cotacaoCompra"),
            payload.get("cotacaoVenda"),
        ]
        for candidate in direct_candidates:
            parsed = CurrencyRateSyncService._to_positive_float(candidate)
            if parsed is not None:
                return parsed

        quotes = payload.get("quotes")
        if isinstance(quotes, dict):
            parsed = CurrencyRateSyncService._to_positive_float(quotes.get("USDBRL"))
            if parsed is not None:
                return parsed

        rates = payload.get("rates")
        if isinstance(rates, dict):
            parsed = CurrencyRateSyncService._to_positive_float(rates.get("BRL"))
            if parsed is not None:
                return parsed

        raise ValueError("Cotacao USD/BRL nao encontrada no payload")

    @staticmethod
    def _extract_date(payload: dict[str, Any], default_date: date) -> date:
        candidates = [
            payload.get("date"),
            payload.get("create_date"),
            payload.get("timestamp"),
            payload.get("dataHoraCotacao"),
        ]
        for candidate in candidates:
            parsed = CurrencyRateSyncService._parse_date(candidate)
            if parsed is not None:
                return parsed
        return default_date

    @staticmethod
    def _to_positive_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(float(value)).date()
        if isinstance(value, str):
            normalized = value.strip().replace("Z", "+00:00")
            for candidate in (normalized, normalized.replace(" ", "T")):
                try:
                    return datetime.fromisoformat(candidate).date()
                except ValueError:
                    continue
            try:
                return date.fromisoformat(normalized[:10])
            except ValueError:
                return None
        return None
