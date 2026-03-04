from __future__ import annotations

from fastapi import APIRouter, Depends

from finops_api.api.v1.deps import get_current_user
from finops_api.api.v1.routers.auth import router as auth_router
from finops_api.api.v1.routers.cloud import router as cloud_router
from finops_api.api.v1.routers.finops import router as finops_router
from finops_api.api.v1.routers.health import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(cloud_router, dependencies=[Depends(get_current_user)])
router.include_router(finops_router, dependencies=[Depends(get_current_user)])
