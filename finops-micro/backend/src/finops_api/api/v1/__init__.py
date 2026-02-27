from __future__ import annotations

from fastapi import APIRouter

from finops_api.api.v1.routers.filters import router as filters_router
from finops_api.api.v1.routers.finops import router as finops_router
from finops_api.api.v1.routers.health import router as health_router
from finops_api.api.v1.routers.summary import router as summary_router
from finops_api.api.v1.routers.timeseries import router as timeseries_router
from finops_api.api.v1.routers.top_services import router as top_services_router

router = APIRouter()
router.include_router(health_router)
router.include_router(filters_router)
router.include_router(finops_router)
router.include_router(summary_router)
router.include_router(timeseries_router)
router.include_router(top_services_router)
