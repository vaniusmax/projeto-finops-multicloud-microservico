from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.models.dim_currency_rate import DimCurrencyRate
from finops_api.models.dim_scope import DimScope
from finops_api.models.dim_service import DimService
from finops_api.models.fact_cost_daily import FactCostDaily


@dataclass
class QueryFilters:
    cloud: str
    start: date
    end: date
    currency: str = "BRL"
    scope_key: str | None = None
    service_key: str | None = None
    services: list[str] | None = None
    accounts: list[str] | None = None


@dataclass
class RankedItem:
    key: str
    name: str
    total: float


class FactCostRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.aws_account_names = self._load_aws_account_names()

    @staticmethod
    def _service_name_expr():
        return func.coalesce(DimService.service_name, FactCostDaily.service_key)

    def _account_name_expr(self):
        resolved_name = self._aws_account_name_case_expr()
        return func.coalesce(
            resolved_name,
            DimScope.scope_name,
            FactCostDaily.scope_key,
        )

    def _aws_account_name_case_expr(self):
        if not self.aws_account_names:
            return None

        whens = []
        for account_id, account_name in self.aws_account_names.items():
            whens.append(
                (
                    (FactCostDaily.cloud == "aws") & (func.coalesce(DimScope.scope_key, FactCostDaily.scope_key) == account_id),
                    literal(account_name),
                )
            )

        return case(*whens, else_=None)

    @staticmethod
    def _load_aws_account_names() -> dict[str, str]:
        try:
            raw = json.loads(settings.aws_account_names_json or "{}")
        except json.JSONDecodeError:
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(key).strip(): str(value).strip() for key, value in raw.items() if str(key).strip()}

    @staticmethod
    def _apply_aws_source_scope(stmt, cloud: str, mode: str):
        if mode == "service":
            if cloud == "aws":
                return stmt.where(
                    FactCostDaily.source_ref == "aws_ce_service_cli"
                ).where(FactCostDaily.service_key != "__ALL__")
            if cloud == "all":
                return stmt.where(
                    (FactCostDaily.cloud != "aws")
                    | (
                        (FactCostDaily.cloud == "aws")
                        & (FactCostDaily.source_ref == "aws_ce_service_cli")
                    )
                ).where((FactCostDaily.cloud != "aws") | (FactCostDaily.service_key != "__ALL__"))
            return stmt
        if mode == "account":
            if cloud == "aws":
                return stmt.where(
                    FactCostDaily.source_ref == "aws_ce_account_cli"
                ).where(FactCostDaily.scope_key != "__ALL__")
            if cloud == "all":
                return stmt.where(
                    (FactCostDaily.cloud != "aws")
                    | (
                        (FactCostDaily.cloud == "aws")
                        & (FactCostDaily.source_ref == "aws_ce_account_cli")
                    )
                ).where((FactCostDaily.cloud != "aws") | (FactCostDaily.scope_key != "__ALL__"))
            return stmt
        return stmt

    def has_source_data_in_range(self, cloud: str, start: date, end: date, source_ref: str) -> bool:
        stmt = (
            select(func.count(FactCostDaily.fact_id))
            .where(FactCostDaily.usage_date.between(start, end))
            .where(FactCostDaily.cloud == cloud)
            .where(FactCostDaily.source_ref == source_ref)
        )
        total = self.db.execute(stmt).scalar_one()
        return int(total or 0) > 0

    def has_source_data_covering_range(self, cloud: str, start: date, end: date, source_ref: str) -> bool:
        stmt = (
            select(func.min(FactCostDaily.usage_date), func.max(FactCostDaily.usage_date))
            .where(FactCostDaily.cloud == cloud)
            .where(FactCostDaily.source_ref == source_ref)
        )
        row = self.db.execute(stmt).one()
        min_date, max_date = row[0], row[1]
        if min_date is None or max_date is None:
            return False
        return min_date <= start and max_date >= end

    def _resolve_brl_per_usd(self, as_of: date) -> float:
        stmt = (
            select(
                DimCurrencyRate.from_currency,
                DimCurrencyRate.to_currency,
                DimCurrencyRate.rate,
            )
            .where(DimCurrencyRate.rate_date <= as_of)
            .order_by(DimCurrencyRate.rate_date.desc())
        )
        rows = self.db.execute(stmt).all()
        for row in rows:
            from_currency = str(row.from_currency or "").upper()
            to_currency = str(row.to_currency or "").upper()
            rate = float(row.rate or 0.0)
            if rate <= 0:
                continue
            if from_currency == "USD" and to_currency == "BRL":
                return rate
            if from_currency == "BRL" and to_currency == "USD":
                return 1.0 / rate
        if settings.usd_rate_fallback and settings.usd_rate_fallback > 0:
            return float(settings.usd_rate_fallback)
        return 1.0

    def _amount_expr(self, currency: str, as_of: date) -> case | Any:
        if currency.upper() == "USD":
            return FactCostDaily.amount
        brl_per_usd = self._resolve_brl_per_usd(as_of)
        return case(
            (FactCostDaily.amount_brl.is_not(None), FactCostDaily.amount_brl),
            (
                FactCostDaily.currency_code == "USD",
                FactCostDaily.amount * literal(brl_per_usd),
            ),
            else_=FactCostDaily.amount,
        )

    @staticmethod
    def _previous_period(filters: QueryFilters) -> QueryFilters:
        range_days = (filters.end - filters.start).days + 1
        prev_end = filters.start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=range_days - 1)
        return QueryFilters(
            cloud=filters.cloud,
            start=prev_start,
            end=prev_end,
            currency=filters.currency,
            scope_key=filters.scope_key,
            service_key=filters.service_key,
            services=filters.services,
            accounts=filters.accounts,
        )

    def _base_stmt(self, filters: QueryFilters, join_service: bool = False, join_scope: bool = False):
        stmt = select(FactCostDaily).where(FactCostDaily.usage_date.between(filters.start, filters.end))
        if filters.cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == filters.cloud)
        if join_service or filters.service_key or filters.services:
            stmt = stmt.join(DimService, DimService.service_id == FactCostDaily.service_id)
        if join_scope or filters.scope_key or filters.accounts:
            stmt = stmt.join(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
        if filters.scope_key:
            stmt = stmt.where(DimScope.scope_key == filters.scope_key)
        if filters.service_key:
            stmt = stmt.where(DimService.service_key == filters.service_key)
        if filters.services:
            stmt = stmt.where(DimService.service_name.in_(filters.services))
        if filters.accounts:
            stmt = stmt.where(DimScope.scope_name.in_(filters.accounts))
        return stmt

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

    def has_data_covering_range(self, cloud: str, start: date, end: date) -> bool:
        stmt = select(func.min(FactCostDaily.usage_date), func.max(FactCostDaily.usage_date))
        if cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == cloud)
        row = self.db.execute(stmt).one()
        min_date, max_date = row[0], row[1]
        if min_date is None or max_date is None:
            return False
        return min_date <= start and max_date >= end

    def total(self, filters: QueryFilters) -> float:
        amount_expr = self._amount_expr(filters.currency, filters.end)
        stmt = (
            select(func.coalesce(func.sum(amount_expr), 0))
            .select_from(FactCostDaily)
            .where(FactCostDaily.usage_date.between(filters.start, filters.end))
        )
        if filters.cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == filters.cloud)
        stmt = self._apply_aws_source_scope(stmt, filters.cloud, "service")
        if filters.scope_key or filters.accounts:
            stmt = stmt.join(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
        if filters.service_key or filters.services:
            stmt = stmt.join(DimService, DimService.service_id == FactCostDaily.service_id)
        if filters.scope_key:
            stmt = stmt.where(DimScope.scope_key == filters.scope_key)
        if filters.service_key:
            stmt = stmt.where(DimService.service_key == filters.service_key)
        if filters.services:
            stmt = stmt.where(DimService.service_name.in_(filters.services))
        if filters.accounts:
            stmt = stmt.where(DimScope.scope_name.in_(filters.accounts))
        value = self.db.execute(stmt).scalar_one()
        return float(value or 0)

    def infer_brl_per_usd(self, filters: QueryFilters) -> float | None:
        stmt = (
            select(
                func.coalesce(func.sum(FactCostDaily.amount_brl), 0).label("sum_brl"),
                func.coalesce(func.sum(FactCostDaily.amount), 0).label("sum_usd"),
            )
            .select_from(FactCostDaily)
            .where(FactCostDaily.usage_date.between(filters.start, filters.end))
            .where(FactCostDaily.amount_brl.is_not(None))
            .where(FactCostDaily.currency_code == "USD")
        )
        if filters.cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == filters.cloud)
        stmt = self._apply_aws_source_scope(stmt, filters.cloud, "service")
        row = self.db.execute(stmt).one()
        sum_brl = float(row.sum_brl or 0.0)
        sum_usd = float(row.sum_usd or 0.0)
        if sum_brl <= 0 or sum_usd <= 0:
            return None
        return sum_brl / sum_usd

    def summary(self, filters: QueryFilters) -> dict:
        current_total = self.total(filters)
        previous_total = self.total(self._previous_period(filters))
        delta_abs = current_total - previous_total
        delta_pct = (delta_abs / previous_total * 100) if previous_total else None
        return {
            "total_current": current_total,
            "total_previous": previous_total,
            "delta": {"absolute": delta_abs, "percent": delta_pct},
        }

    def timeseries(self, filters: QueryFilters) -> list[dict]:
        amount_expr = self._amount_expr(filters.currency, filters.end)
        stmt = (
            select(
                FactCostDaily.usage_date.label("date"),
                func.coalesce(func.sum(amount_expr), 0).label("total"),
            )
            .group_by(FactCostDaily.usage_date)
            .order_by(FactCostDaily.usage_date.asc())
        )
        stmt = self._apply_filters(stmt, filters, join_scope=True, join_service=True)
        stmt = self._apply_aws_source_scope(stmt, filters.cloud, "service")
        rows = self.db.execute(stmt).all()
        return [{"date": row.date, "total": float(row.total or 0)} for row in rows]

    def top_services(self, filters: QueryFilters, limit: int) -> list[RankedItem]:
        amount_expr = self._amount_expr(filters.currency, filters.end)
        service_name = self._service_name_expr()
        service_key = func.coalesce(DimService.service_key, FactCostDaily.service_key)
        stmt = (
            select(
                service_key.label("key"),
                service_name.label("name"),
                func.coalesce(func.sum(amount_expr), 0).label("total"),
            )
            .outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
            .group_by(service_key, service_name)
            .order_by(func.sum(amount_expr).desc())
            .limit(limit)
        )
        stmt = self._apply_filters(
            stmt,
            filters,
            join_scope=True,
            join_service=False,
            scope_joined=False,
            service_joined=True,
        )
        stmt = self._apply_aws_source_scope(stmt, filters.cloud, "service")
        rows = self.db.execute(stmt).all()
        return [RankedItem(key=row.key, name=row.name, total=float(row.total or 0)) for row in rows]

    def top_scopes(self, filters: QueryFilters, limit: int) -> list[RankedItem]:
        amount_expr = self._amount_expr(filters.currency, filters.end)
        account_name = self._account_name_expr()
        account_key = func.coalesce(DimScope.scope_key, FactCostDaily.scope_key)
        stmt = (
            select(
                account_key.label("key"),
                account_name.label("name"),
                func.coalesce(func.sum(amount_expr), 0).label("total"),
            )
            .outerjoin(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
            .group_by(account_key, account_name)
            .order_by(func.sum(amount_expr).desc())
            .limit(limit)
        )
        stmt = self._apply_filters(
            stmt,
            filters,
            join_scope=False,
            join_service=True,
            scope_joined=True,
            service_joined=False,
        )
        rows = self.db.execute(stmt).all()
        return [RankedItem(key=row.key, name=row.name, total=float(row.total or 0)) for row in rows]

    def daily_with_service_breakdown(self, filters: QueryFilters, top_n: int) -> list[dict]:
        amount_expr = self._amount_expr(filters.currency, filters.end)
        service_name = self._service_name_expr()
        count_stmt = (
            select(func.count(func.distinct(service_name)))
            .select_from(FactCostDaily)
            .outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
        )
        count_stmt = self._apply_filters(
            count_stmt,
            filters,
            join_scope=True,
            join_service=False,
            scope_joined=False,
            service_joined=True,
        )
        count_stmt = self._apply_aws_source_scope(count_stmt, filters.cloud, "service")
        distinct_services = int(self.db.execute(count_stmt).scalar_one() or 0)

        has_others = top_n > 1 and distinct_services > top_n
        effective_top_n = max(top_n - 1, 1) if has_others else top_n

        base_stmt = (
            select(service_name.label("service_name"), func.coalesce(func.sum(amount_expr), 0).label("total"))
            .select_from(FactCostDaily)
            .outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
            .group_by(service_name)
            .order_by(func.sum(amount_expr).desc())
            .limit(effective_top_n)
        )
        base_stmt = self._apply_filters(
            base_stmt,
            filters,
            join_scope=True,
            join_service=False,
            scope_joined=False,
            service_joined=True,
        )
        base_stmt = self._apply_aws_source_scope(base_stmt, filters.cloud, "service")
        top_rows = self.db.execute(base_stmt).all()
        top_services = [row.service_name for row in top_rows if row.service_name]

        detail_stmt = (
            select(
                FactCostDaily.usage_date.label("date"),
                service_name.label("service"),
                func.coalesce(func.sum(amount_expr), 0).label("total"),
            )
            .select_from(FactCostDaily)
            .outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
            .group_by(FactCostDaily.usage_date, service_name)
            .order_by(FactCostDaily.usage_date.asc())
        )
        detail_stmt = self._apply_filters(
            detail_stmt,
            filters,
            join_scope=True,
            join_service=False,
            scope_joined=False,
            service_joined=True,
        )
        detail_stmt = self._apply_aws_source_scope(detail_stmt, filters.cloud, "service")
        rows = self.db.execute(detail_stmt).all()

        by_date: dict[date, dict[str, float]] = {}
        for row in rows:
            item_date: date = row.date
            service_name: str = row.service or "N/A"
            bucket = by_date.setdefault(item_date, {"total": 0.0, "byService": {}})
            total_value = float(row.total or 0)
            bucket["total"] += total_value
            key = service_name if (service_name in top_services or not has_others) else "Others"
            bucket["byService"][key] = bucket["byService"].get(key, 0.0) + total_value

        result: list[dict] = []
        for item_date in sorted(by_date.keys()):
            row = by_date[item_date]
            result.append(
                {
                    "date": item_date,
                    "total": row["total"],
                    "byService": row["byService"],
                }
            )
        return result

    def top_services_with_delta(self, filters: QueryFilters, limit: int) -> list[dict]:
        return self._top_ranked_with_delta(filters, limit=limit, group="service", include_others=True)

    def top_accounts_with_delta(self, filters: QueryFilters, limit: int) -> list[dict]:
        return self._top_ranked_with_delta(filters, limit=limit, group="account")

    def filter_lists(self, cloud: str, month: str | None = None) -> dict[str, list[str]]:
        service_name = self._service_name_expr()
        account_name = self._account_name_expr()

        services_stmt = (
            select(service_name.label("service_name"), func.sum(FactCostDaily.amount).label("total"))
            .select_from(FactCostDaily)
            .outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
            .group_by(service_name)
            .order_by(func.sum(FactCostDaily.amount).desc())
            .limit(50)
        )
        accounts_stmt = (
            select(account_name.label("scope_name"), func.sum(FactCostDaily.amount).label("total"))
            .select_from(FactCostDaily)
            .outerjoin(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
            .group_by(account_name)
            .order_by(func.sum(FactCostDaily.amount).desc())
            .limit(50)
        )
        if cloud != "all":
            services_stmt = services_stmt.where(FactCostDaily.cloud == cloud)
            accounts_stmt = accounts_stmt.where(FactCostDaily.cloud == cloud)
            services_stmt = self._apply_aws_source_scope(services_stmt, cloud, "service")
            accounts_stmt = self._apply_aws_source_scope(accounts_stmt, cloud, "account")
        if month:
            year, month_number = month.split("-")
            start = date(int(year), int(month_number), 1)
            end = date(int(year), int(month_number), 28) + timedelta(days=4)
            end = end - timedelta(days=end.day)
            services_stmt = services_stmt.where(FactCostDaily.usage_date.between(start, end))
            accounts_stmt = accounts_stmt.where(FactCostDaily.usage_date.between(start, end))

        services = [row.service_name for row in self.db.execute(services_stmt).all() if row.service_name]
        accounts = [row.scope_name for row in self.db.execute(accounts_stmt).all() if row.scope_name]
        return {"services": services, "accounts": accounts}

    def _top_ranked_with_delta(
        self,
        filters: QueryFilters,
        limit: int,
        group: str,
        include_others: bool = False,
    ) -> list[dict]:
        amount_expr = self._amount_expr(filters.currency, filters.end)
        if group == "service":
            name_col = self._service_name_expr()
            join_scope = True
            join_service = False
            key_name = "serviceName"
        else:
            name_col = self._account_name_expr()
            join_scope = False
            join_service = True
            key_name = "linkedAccount"

        current_stmt = (
            select(name_col.label("name"), func.coalesce(func.sum(amount_expr), 0).label("total"))
            .select_from(FactCostDaily)
            .group_by(name_col)
            .order_by(func.sum(amount_expr).desc())
            .limit(limit - 1 if include_others and limit > 1 else limit)
        )
        if group == "service":
            current_stmt = current_stmt.outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
        else:
            current_stmt = current_stmt.outerjoin(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
        current_stmt = self._apply_filters(
            current_stmt,
            filters,
            join_scope=join_scope,
            join_service=join_service,
            scope_joined=(group == "account"),
            service_joined=(group == "service"),
        )
        current_stmt = self._apply_aws_source_scope(
            current_stmt,
            filters.cloud,
            "service" if group == "service" else "account",
        )
        current_rows = self.db.execute(current_stmt).all()

        prev_filters = self._previous_period(filters)
        prev_stmt = (
            select(name_col.label("name"), func.coalesce(func.sum(amount_expr), 0).label("total"))
            .select_from(FactCostDaily)
            .group_by(name_col)
        )
        if group == "service":
            prev_stmt = prev_stmt.outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
        else:
            prev_stmt = prev_stmt.outerjoin(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
        prev_stmt = self._apply_filters(
            prev_stmt,
            prev_filters,
            join_scope=join_scope,
            join_service=join_service,
            scope_joined=(group == "account"),
            service_joined=(group == "service"),
        )
        prev_stmt = self._apply_aws_source_scope(
            prev_stmt,
            prev_filters.cloud,
            "service" if group == "service" else "account",
        )
        prev_rows = self.db.execute(prev_stmt).all()
        prev_map = {row.name: float(row.total or 0) for row in prev_rows}

        period_total = self.total(filters)
        previous_period_total = self.total(prev_filters)
        result: list[dict] = []
        top_total = 0.0
        top_prev_total = 0.0
        for row in current_rows:
            name = row.name or "N/A"
            total = float(row.total or 0)
            previous_total = prev_map.get(name, 0.0)
            top_total += total
            top_prev_total += previous_total
            delta = total - previous_total
            delta_pct = (delta / previous_total * 100.0) if previous_total > 0 else 0.0
            share_pct = (total / period_total * 100.0) if period_total > 0 else 0.0
            result.append(
                {
                    key_name: name,
                    "total": total,
                    "sharePct": share_pct,
                    "delta": delta,
                    "deltaPct": delta_pct,
                }
            )

        if include_others and period_total > top_total:
            others_total = period_total - top_total
            others_previous_total = max(previous_period_total - top_prev_total, 0.0)
            others_delta = others_total - others_previous_total
            others_delta_pct = (others_delta / others_previous_total * 100.0) if others_previous_total > 0 else 0.0
            result.append(
                {
                    key_name: "Others",
                    "total": others_total,
                    "sharePct": (others_total / period_total * 100.0) if period_total > 0 else 0.0,
                    "delta": others_delta,
                    "deltaPct": others_delta_pct,
                }
            )
        return result

    def _apply_filters(
        self,
        stmt,
        filters: QueryFilters,
        join_scope: bool = False,
        join_service: bool = False,
        scope_joined: bool = False,
        service_joined: bool = False,
    ):
        stmt = stmt.where(FactCostDaily.usage_date.between(filters.start, filters.end))
        if filters.cloud != "all":
            stmt = stmt.where(FactCostDaily.cloud == filters.cloud)
        if (join_scope or filters.scope_key or filters.accounts) and not scope_joined:
            stmt = stmt.outerjoin(DimScope, DimScope.scope_id == FactCostDaily.scope_id)
        if (join_service or filters.service_key or filters.services) and not service_joined:
            stmt = stmt.outerjoin(DimService, DimService.service_id == FactCostDaily.service_id)
        if filters.scope_key:
            stmt = stmt.where(DimScope.scope_key == filters.scope_key)
        if filters.service_key:
            stmt = stmt.where(DimService.service_key == filters.service_key)
        if filters.services:
            stmt = stmt.where(self._service_name_expr().in_(filters.services))
        if filters.accounts:
            stmt = stmt.where(self._account_name_expr().in_(filters.accounts))
        return stmt

    @staticmethod
    def decimal_to_float(value: Decimal | None) -> float:
        return float(value) if value is not None else 0.0
