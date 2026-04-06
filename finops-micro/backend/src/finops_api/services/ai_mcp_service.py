from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.finops import AiInsightResponse, SummaryV2Response
from finops_api.services.analytics_service import AnalyticsService
from finops_api.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

SUPPORTED_CLOUDS = ("aws", "azure", "oci")

CLOUD_ALIASES: dict[str, str] = {
    "aws": "aws",
    "amazon": "aws",
    "azure": "azure",
    "oci": "oci",
    "oracle": "oci",
}

COMPARE_HINTS = (
    "compar",
    " versus ",
    " vs ",
    "diferen",
    "ranking",
    "multicloud",
    "multi-cloud",
    "todas as clouds",
    "all clouds",
    "entre aws",
    "entre azure",
    "entre oci",
)

SQL_HINTS = (
    " sql",
    "sql ",
    " query",
    "consulta",
    "select ",
    "tabela",
    "banco de dados",
)


@dataclass
class ProviderInsight:
    cloud: str
    tenant_key: str | None
    has_data: bool
    summary: SummaryV2Response
    top_services: list[dict[str, Any]]
    sql_top_services: list[dict[str, float | str]]


class AiMcpService:
    def __init__(self, analytics: AnalyticsService) -> None:
        self.analytics = analytics
        self.db: Session = analytics.fact_repo.db

    def generate_if_applicable(
        self,
        filters: QueryFilters,
        question: str,
        top_n: int,
        history: list[dict[str, str]] | None = None,
    ) -> AiInsightResponse | None:
        del history
        normalized_question = f" {question.strip().lower()} "
        compare_intent = any(token in normalized_question for token in COMPARE_HINTS)
        sql_intent = any(token in normalized_question for token in SQL_HINTS)

        if not compare_intent and not sql_intent:
            return None

        target_clouds = self._resolve_target_clouds(normalized_question, selected_cloud=filters.cloud)
        if len(target_clouds) == 1 and not sql_intent:
            return None

        insights = self._collect_provider_insights(
            base_filters=filters,
            clouds=target_clouds,
            top_n=min(max(top_n, 3), 12),
        )
        if not insights:
            return None

        answer = self._build_answer(
            question=question.strip(),
            filters=filters,
            insights=insights,
            include_sql=sql_intent or len(insights) > 1,
        )
        highlights = self._build_highlights(insights)
        actions = self._build_actions(insights)
        return AiInsightResponse(answerMarkdown=answer, highlights=highlights, suggestedActions=actions)

    def _resolve_target_clouds(self, normalized_question: str, selected_cloud: str) -> list[str]:
        explicit_clouds: list[str] = []
        for alias, cloud in CLOUD_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", normalized_question):
                explicit_clouds.append(cloud)

        deduped_explicit = self._stable_unique(explicit_clouds)

        wants_all = "todas as clouds" in normalized_question or "all clouds" in normalized_question or "multicloud" in normalized_question
        if wants_all:
            return list(SUPPORTED_CLOUDS)

        if len(deduped_explicit) >= 2:
            return deduped_explicit

        if selected_cloud == "all":
            return list(SUPPORTED_CLOUDS)

        if deduped_explicit:
            base = [selected_cloud, deduped_explicit[0]]
            return self._stable_unique([item for item in base if item in SUPPORTED_CLOUDS])

        return [selected_cloud] if selected_cloud in SUPPORTED_CLOUDS else list(SUPPORTED_CLOUDS)

    def _collect_provider_insights(self, base_filters: QueryFilters, clouds: list[str], top_n: int) -> list[ProviderInsight]:
        tenant_service = TenantService(self.db)
        insights: list[ProviderInsight] = []

        for cloud in clouds:
            tenant_key = self._resolve_tenant_key_for_cloud(tenant_service, cloud=cloud, base_filters=base_filters)
            tenant_id = None
            if cloud == base_filters.cloud and base_filters.tenant_id is not None:
                tenant_id = base_filters.tenant_id
            elif tenant_key:
                try:
                    tenant = tenant_service.resolve_tenant(cloud, tenant_key)
                    tenant_id = tenant.tenant_id if tenant else None
                except ValueError as exc:
                    logger.warning("MCP: tenant invalido para cloud=%s tenant=%s: %s", cloud, tenant_key, exc)

            provider_filters = QueryFilters(
                cloud=cloud,
                start=base_filters.start,
                end=base_filters.end,
                currency=base_filters.currency,
                tenant_id=tenant_id,
                tenant_key=tenant_key,
                services=base_filters.services,
                accounts=base_filters.accounts,
            )

            has_data = self.analytics.fact_repo.has_data_in_range(
                cloud=cloud,
                start=provider_filters.start,
                end=provider_filters.end,
                tenant_id=provider_filters.tenant_id,
            )

            summary = self._tool_finops_get_summary(provider_filters)
            top_services = self._tool_finops_get_top_services(provider_filters, top_n=top_n)
            sql_top_services = self._tool_sql_run_readonly_top_services(provider_filters, limit=min(top_n, 8))

            insights.append(
                ProviderInsight(
                    cloud=cloud,
                    tenant_key=tenant_key,
                    has_data=has_data,
                    summary=summary,
                    top_services=top_services,
                    sql_top_services=sql_top_services,
                )
            )

        return insights

    def _resolve_tenant_key_for_cloud(
        self,
        tenant_service: TenantService,
        cloud: str,
        base_filters: QueryFilters,
    ) -> str | None:
        if cloud == base_filters.cloud and base_filters.tenant_key:
            return base_filters.tenant_key

        runtime_configs = tenant_service.get_runtime_configs(cloud)
        if not runtime_configs:
            return None
        return runtime_configs[0].tenant_key

    def _tool_finops_get_summary(self, filters: QueryFilters) -> SummaryV2Response:
        return self.analytics.summary_v2(filters)

    def _tool_finops_get_top_services(self, filters: QueryFilters, top_n: int) -> list[dict[str, Any]]:
        return self.analytics.top_services_v2(filters, limit=top_n)

    def _tool_sql_run_readonly_top_services(self, filters: QueryFilters, limit: int) -> list[dict[str, float | str]]:
        conditions = [
            "f.cost_date BETWEEN :start_date AND :end_date",
            "f.cloud = :cloud",
            "(:tenant_id IS NULL OR f.tenant_id = :tenant_id)",
            "(:cloud != 'aws' OR (f.source = 'aws_ce_service_cli' AND f.service_key != '__ALL__'))",
        ]

        if filters.services:
            conditions.append("COALESCE(ds.service_name, f.service_key) IN :services")
        if filters.accounts:
            conditions.append("COALESCE(sc.scope_name, f.scope_key) IN :accounts")

        sql = f"""
            SELECT
              COALESCE(ds.service_name, f.service_key, 'N/A') AS service_name,
              COALESCE(
                SUM(
                  CASE
                    WHEN :currency = 'USD' THEN f.amount
                    WHEN f.amount_brl IS NOT NULL THEN f.amount_brl
                    WHEN f.currency = 'USD' THEN f.amount * :brl_per_usd
                    ELSE f.amount
                  END
                ),
                0
              ) AS total
            FROM fact_cost_daily f
            LEFT JOIN dim_service ds ON ds.service_id = f.service_id
            LEFT JOIN dim_scope sc ON sc.scope_id = f.scope_id
            WHERE {' AND '.join(conditions)}
            GROUP BY COALESCE(ds.service_name, f.service_key, 'N/A')
            ORDER BY total DESC
            LIMIT :limit
        """

        stmt = text(sql)
        if filters.services:
            stmt = stmt.bindparams(bindparam("services", expanding=True))
        if filters.accounts:
            stmt = stmt.bindparams(bindparam("accounts", expanding=True))

        inferred_rate = self.analytics.fact_repo.infer_brl_per_usd(
            QueryFilters(
                cloud=filters.cloud,
                start=filters.start,
                end=filters.end,
                currency=filters.currency,
                tenant_id=filters.tenant_id,
                tenant_key=filters.tenant_key,
                services=filters.services,
                accounts=filters.accounts,
            )
        )
        brl_per_usd = inferred_rate or settings.usd_rate_fallback or 1.0

        params: dict[str, Any] = {
            "start_date": filters.start,
            "end_date": filters.end,
            "cloud": filters.cloud,
            "tenant_id": filters.tenant_id,
            "currency": filters.currency,
            "brl_per_usd": float(brl_per_usd),
            "limit": max(1, min(limit, 20)),
        }
        if filters.services:
            params["services"] = filters.services
        if filters.accounts:
            params["accounts"] = filters.accounts

        rows = self.db.execute(stmt, params).all()
        return [
            {
                "serviceName": str(row.service_name or "N/A"),
                "total": float(row.total or 0.0),
            }
            for row in rows
        ]

    def _build_answer(
        self,
        question: str,
        filters: QueryFilters,
        insights: list[ProviderInsight],
        include_sql: bool,
    ) -> str:
        ordered = sorted(insights, key=lambda item: float(item.summary.totalWeek or 0.0), reverse=True)
        provider_labels = ", ".join(item.cloud.upper() for item in ordered)
        lines = [
            "## Comparacao Multi-Cloud (MCP)",
            f"**Pergunta:** {question}",
            f"**Periodo:** {filters.start.isoformat()} a {filters.end.isoformat()}",
            f"**Moeda:** {filters.currency}",
            f"**Clouds analisadas:** {provider_labels}",
            "",
            "### Resumo por cloud",
        ]

        for item in ordered:
            top_service = item.top_services[0] if item.top_services else None
            top_service_name = str((top_service or {}).get("serviceName") or "sem servico lider")
            top_service_share = float((top_service or {}).get("sharePct") or 0.0)
            tenant_label = item.tenant_key or "(todos)"
            status = "dados disponiveis" if item.has_data else "sem dados no intervalo"

            lines.append(
                (
                    f"- **{item.cloud.upper()}** ({status}) - tenant `{tenant_label}`: "
                    f"total **{self._format_number(item.summary.totalWeek)} {filters.currency}**, "
                    f"delta **{self._format_pct(item.summary.deltaWeek)}**, "
                    f"pico em **{item.summary.peakDay.date.isoformat()}** "
                    f"({self._format_number(item.summary.peakDay.amount)} {filters.currency}), "
                    f"top servico **{top_service_name}** ({self._format_pct(top_service_share)})."
                )
            )

        if len(ordered) >= 2:
            leader = ordered[0]
            runner_up = ordered[1]
            diff_abs = float(leader.summary.totalWeek) - float(runner_up.summary.totalWeek)
            diff_pct = (diff_abs / float(runner_up.summary.totalWeek) * 100.0) if float(runner_up.summary.totalWeek) > 0 else 0.0
            lines.extend(
                [
                    "",
                    "### Diferenca principal",
                    (
                        f"- Lider de custo: **{leader.cloud.upper()}** com vantagem de "
                        f"**{self._format_number(diff_abs)} {filters.currency}** "
                        f"({self._format_pct(diff_pct)}) sobre **{runner_up.cloud.upper()}**."
                    ),
                ]
            )

            service_gap_lines = self._build_service_gap_lines(ordered[0], ordered[1], currency=filters.currency)
            if service_gap_lines:
                lines.append("")
                lines.append("### Maiores divergencias por servico (SQL read-only)")
                lines.extend(service_gap_lines)

        if include_sql:
            lines.extend(
                [
                    "",
                    "### Ferramentas MCP usadas",
                    "- `finops.get_summary`",
                    "- `finops.get_top_services`",
                    "- `sql.run_readonly_top_services`",
                ]
            )

        return "\n".join(lines).strip()

    def _build_service_gap_lines(self, left: ProviderInsight, right: ProviderInsight, currency: str) -> list[str]:
        left_map = {str(item["serviceName"]): float(item["total"]) for item in left.sql_top_services}
        right_map = {str(item["serviceName"]): float(item["total"]) for item in right.sql_top_services}
        service_names = set(left_map) | set(right_map)

        ranked: list[tuple[str, float]] = []
        for service_name in service_names:
            gap = abs(left_map.get(service_name, 0.0) - right_map.get(service_name, 0.0))
            if gap <= 0:
                continue
            ranked.append((service_name, gap))

        ranked.sort(key=lambda item: item[1], reverse=True)
        top_ranked = ranked[:3]

        lines: list[str] = []
        for service_name, _gap in top_ranked:
            left_total = left_map.get(service_name, 0.0)
            right_total = right_map.get(service_name, 0.0)
            delta = left_total - right_total
            owner = left.cloud.upper() if delta >= 0 else right.cloud.upper()
            lines.append(
                (
                    f"- **{service_name}**: {left.cloud.upper()} {self._format_number(left_total)} vs "
                    f"{right.cloud.upper()} {self._format_number(right_total)} {currency} "
                    f"(delta {self._format_number(delta)} {currency}, maior em {owner})."
                )
            )
        return lines

    def _build_highlights(self, insights: list[ProviderInsight]) -> list[str]:
        ordered = sorted(insights, key=lambda item: float(item.summary.totalWeek or 0.0), reverse=True)
        if not ordered:
            return ["Nao foi possivel montar comparacao entre clouds com os dados atuais."]

        highlights: list[str] = []
        leader = ordered[0]
        highlights.append(
            f"{leader.cloud.upper()} lidera o periodo com {self._format_number(leader.summary.totalWeek)}."
        )

        for item in ordered[:3]:
            top_service = item.top_services[0] if item.top_services else None
            if top_service:
                highlights.append(
                    (
                        f"{item.cloud.upper()} tem {top_service.get('serviceName') or 'servico lider'} "
                        f"como principal driver ({self._format_pct(float(top_service.get('sharePct') or 0.0))})."
                    )
                )

        missing = [item.cloud.upper() for item in ordered if not item.has_data]
        if missing:
            highlights.append(f"Sem dados no intervalo para: {', '.join(missing)}.")

        return self._stable_unique(highlights)[:5]

    def _build_actions(self, insights: list[ProviderInsight]) -> list[str]:
        ordered = sorted(insights, key=lambda item: float(item.summary.totalWeek or 0.0), reverse=True)
        if not ordered:
            return ["Ajustar filtros de periodo/cloud e repetir a consulta."]

        leader = ordered[0]
        top_service = leader.top_services[0] if leader.top_services else None
        top_service_name = str((top_service or {}).get("serviceName") or "servico lider")

        actions = [
            f"Priorizar analise de rightsizing no {top_service_name} da cloud {leader.cloud.upper()}.",
            "Executar a mesma pergunta por tenant para separar efeito de compartilhamento entre unidades.",
            "Comparar o mesmo periodo em USD para remover ruido cambial e validar tendencia real.",
            "Rodar pergunta complementar: 'mostre top contas com maior diferenca entre clouds'.",
        ]
        return self._stable_unique(actions)[:5]

    def _format_number(self, value: float) -> str:
        formatted = f"{float(value or 0.0):,.2f}"
        return formatted.replace(",", "§").replace(".", ",").replace("§", ".")

    def _format_pct(self, value: float) -> str:
        return f"{self._format_number(value)}%"

    def _stable_unique(self, items: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for item in items:
            key = item.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped
