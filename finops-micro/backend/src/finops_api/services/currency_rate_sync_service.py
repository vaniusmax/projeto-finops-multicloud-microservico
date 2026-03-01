from __future__ import annotations

import json
import logging
from threading import Lock
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.repositories.currency_rate_repo import CurrencyRateRepository

try:
    from agno.agent import Agent as AgnoAgent
except ImportError:  # pragma: no cover
    AgnoAgent = None  # type: ignore[assignment]

try:
    from agno.models.openai import OpenAIChat
except ImportError:  # pragma: no cover
    OpenAIChat = None  # type: ignore[assignment]

try:
    from agno.tools.yfinance import YFinanceTools
except ImportError:  # pragma: no cover
    YFinanceTools = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class CurrencyQuote:
    rate_date: date
    brl_per_usd: float
    source: str


class CurrencyRateSyncService:
    _request_cache: dict[date, float] = {}
    _cache_lock = Lock()

    def __init__(
        self,
        db: Session,
        repo: CurrencyRateRepository | None = None,
        client: httpx.Client | None = None,
        agent: Any | None = None,
        toolkit: Any | None = None,
    ) -> None:
        self.db = db
        self.repo = repo or CurrencyRateRepository(db)
        self._client = client
        self._agent = agent if agent is not None else self._build_agent()
        self._toolkit = toolkit if toolkit is not None else self._build_toolkit()

    def ensure_brl_usd_rate(self, as_of: date) -> float | None:
        if not settings.currency_rate_sync_on_request:
            return self.repo.get_brl_per_usd(as_of)

        cached = self._request_cache.get(as_of)
        if cached is not None:
            return cached

        with self._cache_lock:
            cached = self._request_cache.get(as_of)
            if cached is not None:
                return cached

            existing = self.repo.get_exact_brl_per_usd(as_of)
            if existing is not None:
                self._request_cache[as_of] = existing
                return existing

            # Provedores de cambio frequentemente ainda nao publicam a taxa do dia corrente.
            # Se ja temos a ultima taxa conhecida para hoje, evitamos chamadas remotas repetidas.
            if as_of >= date.today():
                latest_known = self.repo.get_brl_per_usd(as_of)
                if latest_known is not None:
                    self._request_cache[as_of] = latest_known
                    return latest_known

            quote = self._fetch_quote(as_of)
            if quote is None:
                fallback = self.repo.get_brl_per_usd(as_of)
                if fallback is not None:
                    self._request_cache[as_of] = fallback
                return fallback

            self.repo.upsert_rate(quote.rate_date, "USD", "BRL", quote.brl_per_usd)
            self.repo.upsert_rate(quote.rate_date, "BRL", "USD", 1.0 / quote.brl_per_usd)
            self.db.commit()
            self._request_cache[as_of] = quote.brl_per_usd
            self._request_cache[quote.rate_date] = quote.brl_per_usd
            logger.info(
                "Cotacao USD/BRL sincronizada para %s via %s: %.6f",
                quote.rate_date.isoformat(),
                quote.source,
                quote.brl_per_usd,
            )
            return quote.brl_per_usd

    def _fetch_quote(self, as_of: date) -> CurrencyQuote | None:
        fetchers = self._quote_fetchers(as_of)
        errors: list[str] = []
        for source, fetcher in fetchers:
            try:
                quote = fetcher(as_of)
                if quote is not None:
                    return quote
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source}: {exc}")
        if errors:
            logger.warning("Falha ao sincronizar cotacao USD/BRL: %s", " ; ".join(errors))
            self.db.rollback()
        return None

    def _quote_fetchers(self, as_of: date) -> list[tuple[str, Any]]:
        if as_of >= date.today():
            return [
                ("agno", self._fetch_quote_via_agno),
                ("yfinance", self._fetch_quote_via_yfinance),
                ("http", self._fetch_quote_via_http),
            ]
        return [("http", self._fetch_quote_via_http)]

    def _fetch_quote_via_agno(self, as_of: date) -> CurrencyQuote | None:
        if not settings.currency_rate_agno_enabled:
            return None
        if self._agent is None:
            raise ValueError("AgnoAgent indisponivel ou OpenAI nao configurado")
        prompt = (
            "Use o YFinanceTools para consultar o ultimo preco do ticker BRL=X (USD/BRL). "
            "Responda EXCLUSIVAMENTE com JSON no formato "
            '{"brl_per_usd": <numero_decimal>} sem texto adicional.'
        )
        response = self._agent.run(prompt, stream=False)  # type: ignore[call-arg]
        text = self._extract_agent_text(response)
        payload = json.loads(text)
        rate = self._normalize_brl_per_usd(payload.get("brl_per_usd"))
        if rate is None:
            raise ValueError(f"Retorno invalido do agente: {text!r}")
        return CurrencyQuote(
            rate_date=min(as_of, date.today()),
            brl_per_usd=rate,
            source="agno",
        )

    def _fetch_quote_via_yfinance(self, as_of: date) -> CurrencyQuote | None:
        if not settings.currency_rate_yfinance_enabled:
            return None
        if self._toolkit is None:
            return None
        raw_value = self._toolkit.get_current_stock_price(settings.currency_rate_yfinance_symbol)
        rate = self._normalize_brl_per_usd(raw_value)
        if rate is None:
            raise ValueError(f"Preco YFinance invalido: {raw_value!r}")
        return CurrencyQuote(
            rate_date=min(as_of, date.today()),
            brl_per_usd=rate,
            source="yfinance",
        )

    def _fetch_quote_via_http(self, as_of: date) -> CurrencyQuote:
        response = self._get_client().get(settings.currency_rate_provider_url)
        response.raise_for_status()
        payload = response.json()
        return self._parse_quote(payload, requested_date=as_of)

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        self._client = httpx.Client(timeout=settings.currency_rate_timeout_seconds)
        return self._client

    def _build_agent(self) -> Any | None:
        if not settings.currency_rate_agno_enabled:
            return None
        if AgnoAgent is None or OpenAIChat is None or YFinanceTools is None:
            return None
        if not settings.openai_api_key:
            return None
        try:
            model = OpenAIChat(
                id=settings.openai_model,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base or None,
            )
            return AgnoAgent(
                name="FinOpsExchangeRateAgent",
                model=model,
                tools=[YFinanceTools()],
                telemetry=False,
                markdown=False,
                stream=False,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Falha ao criar AgnoAgent para cotacao: %s", exc)
            return None

    def _build_toolkit(self) -> Any | None:
        if not settings.currency_rate_yfinance_enabled:
            return None
        if YFinanceTools is None:
            return None
        try:
            return YFinanceTools()
        except Exception as exc:  # pragma: no cover
            logger.warning("Falha ao inicializar YFinanceTools: %s", exc)
            return None

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

    @classmethod
    def _normalize_brl_per_usd(cls, value: Any) -> float | None:
        parsed = cls._to_positive_float(value)
        if parsed is None:
            return None
        if parsed < 1:
            inverted = 1.0 / parsed
            return inverted if inverted > 0 else None
        return parsed

    @staticmethod
    def _extract_agent_text(response: Any) -> str:
        if response is None:
            raise ValueError("Resposta vazia do agente")
        if hasattr(response, "get_content_as_string"):
            return str(response.get_content_as_string()).strip()
        content = getattr(response, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(response, str) and response.strip():
            return response.strip()
        raise ValueError("Nao foi possivel extrair texto da resposta do agente")

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
