from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finops_api.api.v1.deps import ensure_auto_ingest_for_filters, get_analytics_service
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.common import TopItem
from finops_api.services.analytics_service import AnalyticsService

router = APIRouter(tags=["top-services"])


@router.get("/top-services", response_model=list[TopItem])
def get_top_services(
    filters: QueryFilters = Depends(ensure_auto_ingest_for_filters),
    limit: int = Query(default=10, ge=1, le=100),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[TopItem]:
    try:
        return [TopItem(**item) for item in service.top_services(filters, limit)]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
