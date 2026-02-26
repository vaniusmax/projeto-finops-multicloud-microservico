from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finops_api.api.v1.deps import ensure_auto_ingest_for_filters, get_analytics_service
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.timeseries import TimeseriesResponse
from finops_api.services.analytics_service import AnalyticsService

router = APIRouter(tags=["timeseries"])


@router.get("/timeseries", response_model=TimeseriesResponse)
def get_timeseries(
    filters: QueryFilters = Depends(ensure_auto_ingest_for_filters),
    granularity: str = Query(default="daily", pattern="^(daily)$"),
    service: AnalyticsService = Depends(get_analytics_service),
) -> TimeseriesResponse:
    try:
        return service.timeseries(filters, granularity)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
