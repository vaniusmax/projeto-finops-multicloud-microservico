from __future__ import annotations

from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.finops import (
    CostExplorerBreakdownItem,
    CostExplorerSnapshotKpi,
    CostExplorerSnapshotResponse,
    CostExplorerTrendItem,
)
from finops_api.services.analytics_service import AnalyticsService


class CostExplorerService:
    def __init__(self, analytics: AnalyticsService) -> None:
        self.analytics = analytics
        self.fact_repo = analytics.fact_repo

    def snapshot(self, filters: QueryFilters, top_n: int) -> CostExplorerSnapshotResponse:
        summary = self.analytics.summary_v2(filters)
        top_services = self.analytics.top_services_v2(filters, limit=top_n)
        top_accounts = self.analytics.top_accounts_v2(filters, limit=top_n)

        largest_service = top_services[0] if top_services else None
        largest_account = top_accounts[0] if top_accounts else None
        top1_share = float((largest_service or {}).get("sharePct") or 0.0)
        top3_share = float(sum(item.get("sharePct") or 0.0 for item in top_services[:3]))

        return CostExplorerSnapshotResponse(
            totalPeriod=float(summary.totalWeek or 0.0),
            deltaPeriodPct=float(summary.deltaWeek or 0.0),
            top1SharePct=top1_share,
            top3SharePct=top3_share,
            peakDay=summary.peakDay,
            largestService=self._to_snapshot_kpi(largest_service, "serviceName"),
            largestAccount=self._to_snapshot_kpi(largest_account, "linkedAccount"),
        )

    def breakdown(self, filters: QueryFilters, top_n: int, group_by: str) -> list[CostExplorerBreakdownItem]:
        return [
            CostExplorerBreakdownItem(**item)
            for item in self.fact_repo.cost_explorer_breakdown(filters, limit=top_n, group_by=group_by)
        ]

    def trend(
        self,
        filters: QueryFilters,
        group_by: str,
        selected_item: str | None,
        top_n: int,
    ) -> list[CostExplorerTrendItem]:
        rows = self.fact_repo.cost_explorer_trend(
            filters,
            group_by=group_by,
            selected_item=selected_item,
            limit=max(min(top_n, 5), 1),
        )
        return [CostExplorerTrendItem(**row) for row in rows]

    @staticmethod
    def _to_snapshot_kpi(item: dict | None, key_name: str) -> CostExplorerSnapshotKpi | None:
        if not item:
            return None
        label = str(item.get(key_name) or "N/A")
        return CostExplorerSnapshotKpi(
            label=label,
            value=float(item.get("total") or 0.0),
            sharePct=float(item.get("sharePct") or 0.0),
            deltaPct=float(item.get("deltaPct") or 0.0),
        )
