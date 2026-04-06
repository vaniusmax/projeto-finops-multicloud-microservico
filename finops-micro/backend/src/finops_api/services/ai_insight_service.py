from __future__ import annotations

import json
import logging
import re
from typing import Any

from finops_api.core.config import settings
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.finops import AiInsightResponse
from finops_api.services.analytics_service import AnalyticsService
from finops_api.services.ai_mcp_service import AiMcpService

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

FINOPS_CHAT_SYSTEM_PROMPT = (
    "Voce e um especialista FinOps senior em ambiente multicloud (AWS, Azure e OCI). "
    "Responda sempre em portugues do Brasil com foco em precisao numerica.\n"
    "REGRAS:\n"
    "1) Use somente os dados presentes no payload JSON.\n"
    "2) Nunca invente numeros, datas, servicos, contas, causas ou percentuais.\n"
    "3) Ao citar valores, preserve moeda e numeros exatamente como no payload.\n"
    "4) Se faltarem dados para responder com precisao, diga claramente quais campos faltam.\n"
    "5) Produza orientacoes FinOps acionaveis (rightsizing, commitment, storage lifecycle e governanca).\n"
    "6) Use o historico apenas para contexto, nunca como fonte numerica.\n"
    "7) Formate numeros com 2 casas decimais e padrao brasileiro (ex.: 15.730,70 e -21,00%).\n"
    "8) Nao use markdown pesado (sem **, tabelas ou blocos). Use texto limpo com quebras de linha.\n"
    "FORMATO DE SAIDA JSON:\n"
    '{'
    '"answerMarkdown":"resposta objetiva em markdown",'
    '"highlights":["item"],'
    '"suggestedActions":["item"]'
    "}\n"
    "Limites: highlights ate 5 itens; suggestedActions ate 5 itens."
)


class AiInsightService:
    def __init__(self, analytics: AnalyticsService) -> None:
        self.analytics = analytics

    def generate(
        self,
        filters: QueryFilters,
        question: str,
        top_n: int,
        history: list[dict[str, str]] | None = None,
    ) -> AiInsightResponse:
        mcp_result = AiMcpService(self.analytics).generate_if_applicable(
            filters=filters,
            question=question,
            top_n=top_n,
            history=history or [],
        )
        if mcp_result is not None:
            return mcp_result
        payload = self._build_payload(filters=filters, question=question, top_n=top_n, history=history or [])
        llm_result = self._generate_with_llm(payload)
        if llm_result is not None:
            return llm_result
        return self._generate_heuristic(payload)

    def _build_payload(
        self,
        filters: QueryFilters,
        question: str,
        top_n: int,
        history: list[dict[str, str]],
    ) -> dict[str, Any]:
        safe_top_n = min(max(top_n, 3), 20)
        summary = self.analytics.summary_v2(filters)
        top_services = self.analytics.top_services_v2(filters, limit=safe_top_n)
        top_accounts = self.analytics.top_accounts_v2(filters, limit=safe_top_n)
        daily = self.analytics.daily_v2(filters, top_n=min(safe_top_n, 12))
        summary_payload = self._round_numbers(summary.model_dump(mode="json"), decimals=2)
        top_services_payload = self._round_numbers(top_services, decimals=2)
        top_accounts_payload = self._round_numbers(top_accounts, decimals=2)
        daily_totals = self._round_numbers(
            [{"date": item.date.isoformat(), "total": float(item.total)} for item in daily],
            decimals=2,
        )
        peak_days = sorted(daily_totals, key=lambda item: item["total"], reverse=True)[:5]
        chat_history = self._normalize_history(history)

        return {
            "question": question.strip(),
            "chat_history": chat_history,
            "filters": {
                "cloud": filters.cloud,
                "from": filters.start.isoformat(),
                "to": filters.end.isoformat(),
                "currency": filters.currency,
                "topN": safe_top_n,
                "services": filters.services or [],
                "accounts": filters.accounts or [],
            },
            "summary": summary_payload,
            "top_services": top_services_payload,
            "top_accounts": top_accounts_payload,
            "daily_totals": daily_totals,
            "peak_days": peak_days,
        }

    def _normalize_history(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        cleaned: list[dict[str, str]] = []
        for item in history[-8:]:
            role = str(item.get("role") or "").strip().lower()
            text = str(item.get("text") or "").strip()
            if role not in {"user", "assistant"} or not text:
                continue
            cleaned.append({"role": role, "text": text[:1500]})
        return cleaned

    def _generate_with_llm(self, payload: dict[str, Any]) -> AiInsightResponse | None:
        if OpenAI is None or not settings.openai_api_key:
            return None
        try:
            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base or None)
            response = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": FINOPS_CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
            )
            content = response.choices[0].message.content if response.choices else None
            if not content:
                return None
            parsed = json.loads(content)
            merged = self._merge_llm_payload(parsed, payload)
            if merged is None:
                return None
            return merged
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao gerar AI insights via LLM: %s", exc)
            return None

    def _merge_llm_payload(self, parsed: dict[str, Any], payload: dict[str, Any]) -> AiInsightResponse | None:
        answer = self._clean_text(str(parsed.get("answerMarkdown") or "").strip())
        if not answer:
            return None

        highlights = self._normalize_text_list(parsed.get("highlights"), limit=5)
        suggested_actions = self._normalize_text_list(parsed.get("suggestedActions"), limit=5)

        if not highlights:
            highlights = self._default_highlights(payload)
        if not suggested_actions:
            suggested_actions = self._default_actions(payload)

        return AiInsightResponse(
            answerMarkdown=answer,
            highlights=highlights,
            suggestedActions=suggested_actions,
        )

    def _normalize_text_list(self, value: Any, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = self._clean_text(str(item).strip())
            if not text:
                continue
            dedupe_key = text.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            normalized.append(text)
            if len(normalized) >= limit:
                break
        return normalized

    def _generate_heuristic(self, payload: dict[str, Any]) -> AiInsightResponse:
        summary = payload["summary"]
        filters = payload["filters"]
        top_services = payload["top_services"]
        top_service = next(iter(top_services), None)
        top_account = next(iter(payload["top_accounts"]), None)
        highest_positive_driver = self._highest_positive_driver(top_services)

        total = float(summary.get("totalWeek") or 0.0)
        delta = float(summary.get("deltaWeek") or 0.0)
        peak_day = summary.get("peakDay") or {}
        peak_date = str(peak_day.get("date") or filters["to"])
        peak_amount = float(peak_day.get("amount") or 0.0)

        top_service_name = str((top_service or {}).get("serviceName") or "sem servico lider")
        top_service_share = float((top_service or {}).get("sharePct") or 0.0)
        top_account_name = str((top_account or {}).get("linkedAccount") or "sem conta lider")
        top_account_share = float((top_account or {}).get("sharePct") or 0.0)

        trend_line = ""
        if highest_positive_driver:
            trend_line = (
                f"O servico com maior alta no periodo foi {highest_positive_driver['serviceName']} "
                f"(delta de {self._format_number(float(highest_positive_driver['delta']))} {filters['currency']} / "
                f"{self._format_pct(float(highest_positive_driver['deltaPct']))})."
            )
        elif delta <= 0:
            trend_line = "Nao houve servico com delta positivo relevante no periodo analisado."

        answer_parts = [
            (
                f"No recorte {filters['from']} a {filters['to']} ({filters['cloud'].upper()}), "
                f"o custo total foi {self._format_number(total)} {filters['currency']} "
                f"com variacao de {self._format_pct(delta)} versus o periodo anterior."
            ),
            f"O pico diario ocorreu em {peak_date} com {self._format_number(peak_amount)} {filters['currency']}.",
            (
                f"O principal servico no periodo foi {top_service_name} ({self._format_pct(top_service_share)} do total) "
                f"e a conta lider foi {top_account_name} ({self._format_pct(top_account_share)} do total)."
            ),
            trend_line,
        ]

        formatted_answer = "\n".join([item for item in answer_parts if item]).strip()
        return AiInsightResponse(
            answerMarkdown=formatted_answer,
            highlights=self._default_highlights(payload),
            suggestedActions=self._default_actions(payload),
        )

    def _default_highlights(self, payload: dict[str, Any]) -> list[str]:
        summary = payload["summary"]
        top_services = payload["top_services"]
        top_service = next(iter(top_services), None)
        top_account = next(iter(payload["top_accounts"]), None)
        highest_positive_driver = self._highest_positive_driver(top_services)
        highlights: list[str] = []

        if top_service:
            highlights.append(
                f"{top_service.get('serviceName') or 'Servico lider'} concentra {self._format_pct(float(top_service.get('sharePct') or 0.0))} do custo."
            )
        if top_account:
            highlights.append(
                f"{top_account.get('linkedAccount') or 'Conta lider'} concentra {self._format_pct(float(top_account.get('sharePct') or 0.0))} do custo."
            )

        peak_day = summary.get("peakDay") or {}
        highlights.append(
            f"Pico diario em {peak_day.get('date') or payload['filters']['to']} com {self._format_number(float(peak_day.get('amount') or 0.0))} {payload['filters']['currency']}."
        )

        if highest_positive_driver:
            highlights.append(
                f"Maior alta no periodo: {highest_positive_driver['serviceName']} ({self._format_number(float(highest_positive_driver['delta']))} {payload['filters']['currency']} / {self._format_pct(float(highest_positive_driver['deltaPct']))})."
            )

        delta = float(summary.get("deltaWeek") or 0.0)
        if delta >= 10:
            highlights.append("A variacao no periodo indica aceleracao relevante de consumo.")
        elif delta <= -10:
            highlights.append("A variacao negativa no periodo indica reducao relevante de consumo.")

        return highlights[:5]

    def _default_actions(self, payload: dict[str, Any]) -> list[str]:
        top_service = next(iter(payload["top_services"]), None)
        top_account = next(iter(payload["top_accounts"]), None)
        top_service_name = str((top_service or {}).get("serviceName") or "servico lider")
        top_account_name = str((top_account or {}).get("linkedAccount") or "conta lider")

        return self._dedupe_items([
            f"Executar rightsizing no {top_service_name} e validar utilizacao real dos recursos.",
            f"Revisar ownership e tagging da conta {top_account_name} para evitar custo sem responsavel.",
            "Avaliar commitment (reservas/savings plans) para workloads estaveis do periodo.",
            "Correlacionar o pico diario com deploys e jobs para eliminar recorrencia de anomalias.",
        ])[:5]

    def _round_numbers(self, value: Any, decimals: int = 2) -> Any:
        if isinstance(value, float):
            return round(value, decimals)
        if isinstance(value, dict):
            return {key: self._round_numbers(item, decimals=decimals) for key, item in value.items()}
        if isinstance(value, list):
            return [self._round_numbers(item, decimals=decimals) for item in value]
        return value

    def _highest_positive_driver(self, top_services: list[dict[str, Any]]) -> dict[str, Any] | None:
        positives = [item for item in top_services if float(item.get("delta") or 0.0) > 0]
        if not positives:
            return None
        return max(positives, key=lambda item: float(item.get("delta") or 0.0))

    def _format_number(self, value: float) -> str:
        formatted = f"{value:,.2f}"
        return formatted.replace(",", "§").replace(".", ",").replace("§", ".")

    def _format_pct(self, value: float) -> str:
        return f"{self._format_number(value)}%"

    def _clean_text(self, text: str) -> str:
        compact = re.sub(r"\*{1,3}", "", text)
        compact = re.sub(r"[ \t]+", " ", compact)
        compact = re.sub(r"\n{3,}", "\n\n", compact)
        compact = re.sub(r"(?<![\d,])([+-]?\d+\.\d{3,})(?![\d,])", self._round_decimal_match, compact)
        return compact.strip()

    def _round_decimal_match(self, match: re.Match[str]) -> str:
        return f"{float(match.group(1)):.2f}"

    def _dedupe_items(self, items: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for item in items:
            normalized = self._clean_text(item)
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(normalized)
        return deduped
