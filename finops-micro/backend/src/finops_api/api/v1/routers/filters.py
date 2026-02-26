from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finops_api.api.v1.deps import get_filters_service
from finops_api.schemas.filters import FiltersResponse
from finops_api.services.filters_service import FiltersService

router = APIRouter(tags=["filters"])


@router.get("/filters", response_model=FiltersResponse)
def get_filters(
    cloud: str = Query(default="all", pattern="^(aws|azure|oci|all)$"),
    service: FiltersService = Depends(get_filters_service),
) -> FiltersResponse:
    try:
        return service.get_filters(cloud=cloud)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
