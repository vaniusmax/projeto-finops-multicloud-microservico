from __future__ import annotations

from finops_api.repositories.fact_cost_repo import FactCostRepository, QueryFilters
from finops_api.schemas.summary import SummaryResponse
from finops_api.schemas.timeseries import TimeseriesPoint, TimeseriesResponse


class AnalyticsService:
    def __init__(self, fact_repo: FactCostRepository) -> None:
        self.fact_repo = fact_repo

    def summary(self, filters: QueryFilters) -> SummaryResponse:
        base = self.fact_repo.summary(filters)
        top_services = self.fact_repo.top_services(filters, limit=5)
        top_scopes = self.fact_repo.top_scopes(filters, limit=5)
        return SummaryResponse(
            total_current=base["total_current"],
            total_previous=base["total_previous"],
            delta=base["delta"],
            top_services=[item.__dict__ for item in top_services],
            top_scopes=[item.__dict__ for item in top_scopes],
        )

    def timeseries(self, filters: QueryFilters, granularity: str) -> TimeseriesResponse:
        # TODO: mapear variantes do legado para agregações semanal/mensal quando necessário.
        points = self.fact_repo.timeseries(filters)
        return TimeseriesResponse(
            granularity=granularity,
            points=[TimeseriesPoint(**point) for point in points],
        )

    def top_services(self, filters: QueryFilters, limit: int) -> list[dict]:
        rows = self.fact_repo.top_services(filters, limit=limit)
        return [item.__dict__ for item in rows]
