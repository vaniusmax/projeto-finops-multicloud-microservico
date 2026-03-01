from __future__ import annotations

import json
import logging
from typing import Any

from finops_api.core.config import settings
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.finops import (
    CostExplorerInsightAction,
    CostExplorerInsightEvidence,
    CostExplorerInsightResponse,
    CostExplorerNextDrilldown,
)
from finops_api.services.cost_explorer_service import CostExplorerService

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class CostExplorerInsightService:
    def __init__(self, cost_explorer: CostExplorerService) -> None:
        self.cost_explorer = cost_explorer

    def generate(
        self,
        filters: QueryFilters,
        top_n: int,
        group_by: str,
        selected_item: str | None,
    ) -> CostExplorerInsightResponse:
        payload = self._build_payload(filters, top_n=top_n, group_by=group_by, selected_item=selected_item)
        llm_result = self._generate_with_llm(payload)
        if llm_result is not None:
            return llm_result
        return self._generate_heuristic(payload)

    def _build_payload(
        self,
        filters: QueryFilters,
        top_n: int,
        group_by: str,
        selected_item: str | None,
    ) -> dict[str, Any]:
        snapshot = self.cost_explorer.snapshot(filters, top_n=top_n)
        breakdown = self.cost_explorer.breakdown(filters, top_n=top_n, group_by=group_by)
        active_item = selected_item or (breakdown[0].label if breakdown else None)
        trend = self.cost_explorer.trend(filters, group_by=group_by, selected_item=active_item, top_n=top_n)
        return {
            "filters": {
                "cloud": filters.cloud,
                "from": filters.start.isoformat(),
                "to": filters.end.isoformat(),
                "currency": filters.currency,
                "topN": top_n,
                "groupBy": group_by,
                "selectedItem": active_item,
                "services": filters.services or [],
                "accounts": filters.accounts or [],
            },
            "snapshot": snapshot.model_dump(mode="json"),
            "breakdown": [item.model_dump(mode="json") for item in breakdown],
            "trend": [item.model_dump(mode="json") for item in trend],
        }

    def _generate_with_llm(self, payload: dict[str, Any]) -> CostExplorerInsightResponse | None:
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
                            "Voce e um especialista FinOps em investigacao de custo. "
                            "Use SOMENTE o payload fornecido. "
                            "Nao invente numeros, causas ou entidades nao presentes. "
                            "Responda em JSON com as chaves: summary, drivers, risks, actions, suggestedQuestions, nextDrilldowns. "
                            "actions deve conter title, owner, priority, rationale. "
                            "nextDrilldowns deve conter dimension, value, reason."
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
            )
            content = response.choices[0].message.content if response.choices else None
            if not content:
                return None
            parsed = json.loads(content)
            return self._merge_llm_payload(parsed, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao gerar cost explorer insights via LLM: %s", exc)
            return None

    def _merge_llm_payload(self, parsed: dict[str, Any], payload: dict[str, Any]) -> CostExplorerInsightResponse:
        actions = [
            CostExplorerInsightAction(
                title=str(item.get("title") or "Acao sugerida"),
                owner=str(item.get("owner") or "FinOps"),
                priority=str(item.get("priority") or "media"),
                rationale=str(item.get("rationale") or "Sem racional informado."),
            )
            for item in (parsed.get("actions") or [])[:4]
            if isinstance(item, dict)
        ]
        next_drilldowns = [
            CostExplorerNextDrilldown(
                dimension=str(item.get("dimension") or "service"),
                value=str(item.get("value") or ""),
                reason=str(item.get("reason") or "Maior relevancia no recorte."),
            )
            for item in (parsed.get("nextDrilldowns") or [])[:4]
            if isinstance(item, dict) and item.get("value")
        ]
        return CostExplorerInsightResponse(
            mode="llm",
            summary=str(parsed.get("summary") or ""),
            drivers=[str(item) for item in (parsed.get("drivers") or [])[:5]],
            risks=[str(item) for item in (parsed.get("risks") or [])[:4]],
            actions=actions,
            suggestedQuestions=[str(item) for item in (parsed.get("suggestedQuestions") or [])[:5]],
            nextDrilldowns=next_drilldowns,
            evidence=self._build_evidence(payload),
        )

    def _generate_heuristic(self, payload: dict[str, Any]) -> CostExplorerInsightResponse:
        snapshot = payload["snapshot"]
        breakdown = payload["breakdown"]
        filters = payload["filters"]
        selected_item = str(filters.get("selectedItem") or "")
        focus = breakdown[0] if breakdown else None
        focus_label = selected_item or str((focus or {}).get("label") or "item líder")
        focus_share = float((focus or {}).get("sharePct") or 0.0)
        total = float(snapshot.get("totalPeriod") or 0.0)
        delta = float(snapshot.get("deltaPeriodPct") or 0.0)

        summary = (
            f"O recorte totaliza {total:,.2f} em {filters['currency']} e está concentrado em {focus_label}, "
            f"que representa {focus_share:.1f}% do custo no agrupamento por {filters['groupBy']}."
        )
        drivers = [
            f"O top 1 concentra {float(snapshot.get('top1SharePct') or 0.0):.1f}% do total.",
            f"O top 3 concentra {float(snapshot.get('top3SharePct') or 0.0):.1f}% do total.",
        ]
        if delta > 10:
            drivers.append("A variação positiva do período indica aceleração relevante de consumo.")
        elif delta < -10:
            drivers.append("A redução do período sugere mudança operacional ou ganho de eficiência.")
        if selected_item:
            drivers.append(f"{selected_item} foi promovido como foco principal para o próximo drilldown.")

        risks = []
        if float(snapshot.get("top1SharePct") or 0.0) >= 30:
            risks.append("Existe concentração relevante em um único item do breakdown atual.")
        if float(snapshot.get("top3SharePct") or 0.0) >= 70:
            risks.append("Poucos itens concentram a maior parte do custo; o risco de dependência é alto.")
        peak_day = snapshot.get("peakDay") or {}
        if float(peak_day.get("amount") or 0.0) > 0 and focus_share >= 20:
            risks.append("O pico diário merece correlação com o item líder para confirmar causalidade.")
        if not risks:
            risks.append("O recorte parece distribuído, mas ainda vale revisar os maiores itens e o pico diário.")

        largest_account = (snapshot.get("largestAccount") or {}).get("label") or "conta líder"
        group_dimension = "conta" if filters["groupBy"] == "service" else "serviço"
        next_drilldowns = [
            CostExplorerNextDrilldown(
                dimension="account" if filters["groupBy"] == "service" else "service",
                value=str(largest_account if filters["groupBy"] == "service" else focus_label),
                reason="Maior concentração observada no recorte atual.",
            )
        ]
        actions = [
            CostExplorerInsightAction(
                title=f"Quebrar {focus_label} por {group_dimension}",
                owner="FinOps + Owner técnico",
                priority="alta",
                rationale="Item líder do período deve ser explicado pelos próximos níveis de agregação.",
            ),
            CostExplorerInsightAction(
                title="Correlacionar pico diário com mudanças operacionais",
                owner="Operações",
                priority="media",
                rationale="Picos diários costumam indicar deploys, cargas pontuais ou anomalias replicáveis.",
            ),
            CostExplorerInsightAction(
                title="Revisar oportunidades de rightsizing e commitment",
                owner="FinOps",
                priority="media",
                rationale="Serviços e contas líderes normalmente concentram o maior potencial de otimização.",
            ),
        ]
        questions = [
            f"O que explica a liderança de {focus_label} neste recorte?",
            f"Quais dias concentraram o custo de {focus_label}?",
            f"Qual {group_dimension} explica melhor o crescimento observado?",
            "Existe oportunidade rápida de redução nos itens líderes?",
        ]

        return CostExplorerInsightResponse(
            mode="heuristic",
            summary=summary,
            drivers=drivers[:5],
            risks=risks[:4],
            actions=actions[:4],
            suggestedQuestions=questions[:5],
            nextDrilldowns=next_drilldowns,
            evidence=self._build_evidence(payload),
        )

    def _build_evidence(self, payload: dict[str, Any]) -> CostExplorerInsightEvidence:
        snapshot = payload["snapshot"]
        breakdown = payload["breakdown"]
        return CostExplorerInsightEvidence(
            groupBy=str(payload["filters"].get("groupBy") or "service"),
            selectedItem=payload["filters"].get("selectedItem"),
            totalPeriod=float(snapshot.get("totalPeriod") or 0.0),
            deltaPeriodPct=float(snapshot.get("deltaPeriodPct") or 0.0),
            peakDay=(snapshot.get("peakDay") or {}).get("date"),
            topBreakdown=[str(item.get("label")) for item in breakdown[:3] if item.get("label")],
            topServices=[
                str((snapshot.get("largestService") or {}).get("label"))
            ]
            if (snapshot.get("largestService") or {}).get("label")
            else [],
            topAccounts=[
                str((snapshot.get("largestAccount") or {}).get("label"))
            ]
            if (snapshot.get("largestAccount") or {}).get("label")
            else [],
        )
