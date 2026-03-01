from __future__ import annotations

import json
import logging
from typing import Any

from finops_api.core.config import settings
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.finops import (
    AnalyticsInsightAction,
    AnalyticsInsightEvidence,
    AnalyticsInsightResponse,
)
from finops_api.services.analytics_service import AnalyticsService

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class AnalyticsInsightService:
    def __init__(self, analytics: AnalyticsService) -> None:
        self.analytics = analytics

    def generate(self, filters: QueryFilters, top_n: int) -> AnalyticsInsightResponse:
        payload = self._build_payload(filters, top_n)
        llm_result = self._generate_with_llm(payload)
        if llm_result is not None:
            return llm_result
        return self._generate_heuristic(payload)

    def _build_payload(self, filters: QueryFilters, top_n: int) -> dict[str, Any]:
        summary = self.analytics.summary_v2(filters)
        top_services = self.analytics.top_services_v2(filters, limit=top_n)
        top_accounts = self.analytics.top_accounts_v2(filters, limit=top_n)
        daily = self.analytics.daily_v2(filters, top_n=top_n)
        return {
            "filters": {
                "cloud": filters.cloud,
                "from": filters.start.isoformat(),
                "to": filters.end.isoformat(),
                "currency": filters.currency,
                "topN": top_n,
                "services": filters.services or [],
                "accounts": filters.accounts or [],
            },
            "summary": summary.model_dump(mode="json"),
            "top_services": top_services,
            "top_accounts": top_accounts,
            "daily": [item.model_dump(mode="json") for item in daily],
        }

    def _generate_with_llm(self, payload: dict[str, Any]) -> AnalyticsInsightResponse | None:
        if OpenAI is None or not settings.openai_api_key:
            return None
        try:
            client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_api_base or None)
            response = client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Voce e um analista FinOps senior. "
                            "Use SOMENTE o payload fornecido. "
                            "Nao invente numeros, datas ou entidades. "
                            "Responda em JSON com as chaves: summary, drivers, risks, actions, suggestedQuestions. "
                            "actions deve conter objetos com title, owner, priority, rationale."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False),
                    },
                ],
            )
            content = response.choices[0].message.content if response.choices else None
            if not content:
                return None
            parsed = json.loads(content)
            return self._merge_llm_payload(parsed, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao gerar analytics insights via LLM: %s", exc)
            return None

    def _merge_llm_payload(self, parsed: dict[str, Any], payload: dict[str, Any]) -> AnalyticsInsightResponse:
        evidence = self._build_evidence(payload)
        actions = [
            AnalyticsInsightAction(
                title=str(item.get("title") or "Acao sugerida"),
                owner=str(item.get("owner") or "FinOps"),
                priority=str(item.get("priority") or "media"),
                rationale=str(item.get("rationale") or "Sem racional informado."),
            )
            for item in (parsed.get("actions") or [])[:4]
            if isinstance(item, dict)
        ]
        return AnalyticsInsightResponse(
            mode="llm",
            summary=str(parsed.get("summary") or ""),
            drivers=[str(item) for item in (parsed.get("drivers") or [])[:5]],
            risks=[str(item) for item in (parsed.get("risks") or [])[:4]],
            actions=actions,
            suggestedQuestions=[str(item) for item in (parsed.get("suggestedQuestions") or [])[:4]],
            evidence=evidence,
        )

    def _generate_heuristic(self, payload: dict[str, Any]) -> AnalyticsInsightResponse:
        summary = payload["summary"]
        top_service = next(iter(payload["top_services"]), None)
        top_account = next(iter(payload["top_accounts"]), None)
        total = float(summary.get("totalWeek") or 0.0)
        delta = float(summary.get("deltaWeek") or 0.0)
        top_service_name = str((top_service or {}).get("serviceName") or "sem serviço líder")
        top_account_name = str((top_account or {}).get("linkedAccount") or "sem conta líder")
        summary_text = (
            f"O período totalizou {total:,.2f} em {payload['filters']['currency']}, com variação de {delta:.2f}% "
            f"vs período anterior. O maior driver atual é {top_service_name}, concentrado principalmente em {top_account_name}."
        )
        drivers = []
        if top_service:
            drivers.append(
                f"{top_service_name} responde por {float(top_service.get('sharePct') or 0.0):.1f}% do total analisado."
            )
        if top_account:
            drivers.append(
                f"{top_account_name} concentra {float(top_account.get('sharePct') or 0.0):.1f}% do custo no recorte."
            )
        if delta > 10:
            drivers.append("A variação do período sugere aceleração relevante de consumo e merece investigação imediata.")
        elif delta < -10:
            drivers.append("A queda expressiva sugere ganho de eficiência ou mudança de carga que deve ser validada.")

        risks = []
        if top_account and float(top_account.get("sharePct") or 0.0) >= 40:
            risks.append("Existe alta concentração de custo em uma única conta.")
        if top_service and float(top_service.get("sharePct") or 0.0) >= 35:
            risks.append("O custo está excessivamente dependente de um único serviço.")
        if float(summary.get("avgDaily") or 0.0) > 0 and float(summary["peakDay"]["amount"]) > float(summary.get("avgDaily") or 0.0) * 1.3:
            risks.append("O pico diário está significativamente acima da média diária do período.")
        if not risks:
            risks.append("Nao ha risco dominante obvio no recorte atual, mas vale acompanhar concentracao por conta e servico.")

        actions = [
            AnalyticsInsightAction(
                title=f"Revisar consumo de {top_service_name}",
                owner="FinOps + Plataforma",
                priority="alta",
                rationale="Servico lidera o ranking do período e deve ser quebrado por ambiente, uso e direito de sizing.",
            ),
            AnalyticsInsightAction(
                title=f"Validar alocacao da conta {top_account_name}",
                owner="FinOps + Owner da conta",
                priority="alta",
                rationale="Conta concentra a maior parcela do custo e pode esconder cargas fora do padrão esperado.",
            ),
            AnalyticsInsightAction(
                title="Correlacionar pico diário com deploys e jobs",
                owner="Operacoes",
                priority="media",
                rationale="Picos acima da média costumam indicar eventos operacionais identificáveis.",
            ),
        ]
        questions = [
            f"Quais SKUs dentro de {top_service_name} mais cresceram no período?",
            f"O que explica a participação da conta {top_account_name} no total?",
            "Quais dias concentraram a maior parte da variação semanal?",
            "Existe oportunidade rápida de rightsizing nos serviços líderes?",
        ]

        return AnalyticsInsightResponse(
            mode="heuristic",
            summary=summary_text,
            drivers=drivers[:5],
            risks=risks[:4],
            actions=actions[:4],
            suggestedQuestions=questions[:4],
            evidence=self._build_evidence(payload),
        )

    def _build_evidence(self, payload: dict[str, Any]) -> AnalyticsInsightEvidence:
        summary = payload["summary"]
        return AnalyticsInsightEvidence(
            topServices=[
                str(item.get("serviceName"))
                for item in payload["top_services"][:3]
                if item.get("serviceName")
            ],
            topAccounts=[
                str(item.get("linkedAccount"))
                for item in payload["top_accounts"][:3]
                if item.get("linkedAccount")
            ],
            peakDay=summary["peakDay"]["date"],
            totalPeriod=float(summary.get("totalWeek") or 0.0),
            deltaPeriodPct=float(summary.get("deltaWeek") or 0.0),
        )
