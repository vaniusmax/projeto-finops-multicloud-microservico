from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finops_api.models.dim_region import DimRegion
from finops_api.models.dim_scope import DimScope
from finops_api.models.dim_service import DimService
from finops_api.models.fact_cost_daily import FactCostDaily


@dataclass
class Item:
    key: str
    name: str


class DimsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_scopes_by_cloud(self) -> dict[str, list[Item]]:
        stmt = select(DimScope.cloud, DimScope.scope_key, DimScope.scope_name).order_by(
            DimScope.cloud.asc(),
            DimScope.scope_name.asc(),
        )
        rows = self.db.execute(stmt).all()
        grouped: dict[str, list[Item]] = {"aws": [], "azure": [], "oci": []}
        for cloud, scope_key, scope_name in rows:
            grouped.setdefault(cloud, []).append(Item(key=scope_key, name=scope_name))
        return grouped

    def top_services(self, cloud: str | None, limit: int = 10) -> list[Item]:
        stmt = (
            select(DimService.service_key, DimService.service_name, func.sum(FactCostDaily.amount).label("total"))
            .join(FactCostDaily, FactCostDaily.service_id == DimService.service_id)
            .group_by(DimService.service_key, DimService.service_name)
            .order_by(func.sum(FactCostDaily.amount).desc())
            .limit(limit)
        )
        if cloud:
            stmt = stmt.where(FactCostDaily.cloud == cloud)
        rows = self.db.execute(stmt).all()
        return [Item(key=row.service_key, name=row.service_name) for row in rows]

    def top_regions(self, cloud: str | None, limit: int = 10) -> list[Item]:
        stmt = (
            select(DimRegion.region_key, DimRegion.region_name, func.sum(FactCostDaily.amount).label("total"))
            .join(FactCostDaily, FactCostDaily.region_id == DimRegion.region_id)
            .group_by(DimRegion.region_key, DimRegion.region_name)
            .order_by(func.sum(FactCostDaily.amount).desc())
            .limit(limit)
        )
        if cloud:
            stmt = stmt.where(FactCostDaily.cloud == cloud)
        rows = self.db.execute(stmt).all()
        return [Item(key=row.region_key, name=row.region_name) for row in rows]
