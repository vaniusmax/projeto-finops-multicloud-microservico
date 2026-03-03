from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from finops_api.db.session import get_db
from finops_api.schemas.finops import TenantOption
from finops_api.services.tenant_service import TenantService

router = APIRouter(prefix="/cloud", tags=["cloud"])


@router.get("/{cloud}/tenants", response_model=list[TenantOption])
def get_cloud_tenants(cloud: str, db: Session = Depends(get_db)) -> list[TenantOption]:
    if cloud not in {"aws", "azure", "oci"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cloud inválida")
    tenants = TenantService(db).list_tenants(cloud)
    return [
        TenantOption(
            tenantKey=tenant.tenant_key,
            tenantName=tenant.tenant_name or tenant.tenant_key,
            cloud=tenant.cloud,
        )
        for tenant in tenants
    ]
