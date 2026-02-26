from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from finops_api.api.v1.deps import ensure_auto_ingest_for_filters, get_analytics_service
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.summary import SummaryResponse
from finops_api.services.analytics_service import AnalyticsService

router = APIRouter(tags=["summary"])


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    filters: QueryFilters = Depends(ensure_auto_ingest_for_filters),
    service: AnalyticsService = Depends(get_analytics_service),
) -> SummaryResponse:
    try:
        return service.summary(filters)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
