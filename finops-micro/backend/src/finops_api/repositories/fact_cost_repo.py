from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from finops_api.models.dim_scope import DimScope
from finops_api.models.dim_service import DimService
from finops_api.models.fact_cost_daily import FactCostDaily


@dataclass
class QueryFilters:
    cloud: str
    start: date
    end: date
    scope_key: str | None = None
    service_key: str | None = None


@dataclass
class RankedItem:
    key: str
    name: str
    total: float


class FactCostRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _amount_expr() -> case:
        return case(
            (FactCostDaily.amount_brl.is_not(None), FactCostDaily.amount_brl),
            else_=FactCostDaily.amount,
        )

    def available_range(self, cloud: str) -> tuple[date | None, date | None]:
        stmt = select(func.min(FactCostDaily.usage_date), func.max(FactCostDaily.usage_date))
        if cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == cloud)
        row = self.db.execute(stmt).one()
        return row[0], row[1]

    def has_data_in_range(self, cloud: str, start: date, end: date) -> bool:
        stmt = select(func.count(FactCostDaily.fact_id)).where(FactCostDaily.usage_date.between(start, end))
        if cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == cloud)
        total = self.db.execute(stmt).scalar_one()
        return int(total or 0) > 0

    def total(self, filters: QueryFilters) -> float:
        amount_expr = self._amount_expr()
        stmt = select(func.coalesce(func.sum(amount_expr), 0)).select_from(FactCostDaily)
        stmt = self._apply_filters(stmt, filters)
        value = self.db.execute(stmt).scalar_one()
        return float(value or 0)

    def summary(self, filters: QueryFilters) -> dict:
        current_total = self.total(filters)
        range_days = (filters.end - filters.start).days + 1
        prev_end = filters.start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=range_days - 1)
        previous_total = self.total(
            QueryFilters(
                cloud=filters.cloud,
                start=prev_start,
                end=prev_end,
                scope_key=filters.scope_key,
                service_key=filters.service_key,
            )
        )
        delta_abs = current_total - previous_total
        delta_pct = (delta_abs / previous_total * 100) if previous_total else None
        return {
            "total_current": current_total,
            "total_previous": previous_total,
            "delta": {"absolute": delta_abs, "percent": delta_pct},
        }

    def timeseries(self, filters: QueryFilters) -> list[dict]:
        amount_expr = self._amount_expr()
        stmt = (
            select(
                FactCostDaily.usage_date.label("date"),
                func.coalesce(func.sum(amount_expr), 0).label("total"),
            )
            .group_by(FactCostDaily.usage_date)
            .order_by(FactCostDaily.usage_date.asc())
        )
        stmt = self._apply_filters(stmt, filters)
        rows = self.db.execute(stmt).all()
        return [{"date": row.date, "total": float(row.total or 0)} for row in rows]

    def top_services(self, filters: QueryFilters, limit: int) -> list[RankedItem]:
        amount_expr = self._amount_expr()
        stmt = (
            select(
                DimService.service_key.label("key"),
                DimService.service_name.label("name"),
                func.coalesce(func.sum(amount_expr), 0).label("total"),
            )
            .join(DimService, DimService.service_id == FactCostDaily.service_id)
            .group_by(DimService.service_key, DimService.service_name)
            .order_by(func.sum(amount_expr).desc())
            .limit(limit)
        )
        stmt = self._apply_filters(stmt, filters)
        rows = self.db.execute(stmt).all()
        return [RankedItem(key=row.key, name=row.name, total=float(row.total or 0)) for row in rows]

    def top_scopes(self, filters: QueryFilters, limit: int) -> list[RankedItem]:
        amount_expr = self._amount_expr()
        stmt = (
            select(
                DimScope.scope_key.label("key"),
                DimScope.scope_name.label("name"),
                func.coalesce(func.sum(amount_expr), 0).label("total"),
            )
            .join(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
            .group_by(DimScope.scope_key, DimScope.scope_name)
            .order_by(func.sum(amount_expr).desc())
            .limit(limit)
        )
        stmt = self._apply_filters(stmt, filters)
        rows = self.db.execute(stmt).all()
        return [RankedItem(key=row.key, name=row.name, total=float(row.total or 0)) for row in rows]

    def _apply_filters(self, stmt, filters: QueryFilters):
        stmt = stmt.where(FactCostDaily.usage_date.between(filters.start, filters.end))
        if filters.cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == filters.cloud)
        if filters.scope_key:
            stmt = stmt.join(DimScope, DimScope.scope_id == FactCostDaily.scope_id).where(
                DimScope.scope_key == filters.scope_key
            )
        if filters.service_key:
            stmt = stmt.join(DimService, DimService.service_id == FactCostDaily.service_id).where(
                DimService.service_key == filters.service_key
            )
        return stmt

    @staticmethod
    def decimal_to_float(value: Decimal | None) -> float:
        return float(value) if value is not None else 0.0
