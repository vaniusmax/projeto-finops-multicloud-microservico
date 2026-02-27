from __future__ import annotations

from datetime import date, timedelta

from finops_api.core.config import settings
from finops_api.repositories.currency_rate_repo import CurrencyRateRepository
from finops_api.repositories.fact_cost_repo import FactCostRepository, QueryFilters
from finops_api.schemas.finops import (
    DailyItem,
    PeakDay,
    SummaryV2Response,
)
from finops_api.schemas.summary import SummaryResponse
from finops_api.schemas.timeseries import TimeseriesPoint, TimeseriesResponse
from finops_api.services.targets_service import TargetsService


class AnalyticsService:
    def __init__(
        self,
        fact_repo: FactCostRepository,
        currency_repo: CurrencyRateRepository | None = None,
        targets: TargetsService | None = None,
    ) -> None:
        self.fact_repo = fact_repo
        self.currency_repo = currency_repo
        self.targets = targets or TargetsService()

    def summary(self, filters: QueryFilters) -> SummaryResponse:
        base = self.fact_repo.summary(filters)
        top_services = self.fact_repo.top_services(filters, limit=5)
        top_scopes = self.fact_repo.top_scopes(filters, limit=5)
        return SummaryResponse(
            total_current=base["total_current"],
            total_previous=base["total_previous"],
            delta=base["delta"],
            top_services=[item.__dict__ for item in top_services],
            top_scopes=[item.__dict__ for item in top_scopes],
        )

    def timeseries(self, filters: QueryFilters, granularity: str) -> TimeseriesResponse:
        # TODO: mapear variantes do legado para agregações semanal/mensal quando necessário.
        points = self.fact_repo.timeseries(filters)
        return TimeseriesResponse(
            granularity=granularity,
            points=[TimeseriesPoint(**point) for point in points],
        )

    def top_services(self, filters: QueryFilters, limit: int) -> list[dict]:
        rows = self.fact_repo.top_services(filters, limit=limit)
        return [item.__dict__ for item in rows]

    def summary_v2(self, filters: QueryFilters) -> SummaryV2Response:
        week_total = self.fact_repo.total(filters)
        week_days = max((filters.end - filters.start).days + 1, 1)
        avg_daily = week_total / week_days

        prev_filters = QueryFilters(
            cloud=filters.cloud,
            start=filters.start - timedelta(days=week_days),
            end=filters.start - timedelta(days=1),
            currency=filters.currency,
            services=filters.services,
            accounts=filters.accounts,
        )
        prev_total = self.fact_repo.total(prev_filters)
        delta_pct = ((week_total - prev_total) / prev_total * 100.0) if prev_total > 0 else 0.0

        daily = self.fact_repo.timeseries(filters)
        peak = max(daily, key=lambda item: item["total"]) if daily else {"date": filters.start, "total": 0.0}
        peak_day = PeakDay(date=peak["date"], amount=peak["total"])

        reference_date = date.today()
        month_start = reference_date.replace(day=1)
        month_filters = QueryFilters(
            cloud=filters.cloud,
            start=month_start,
            end=reference_date,
            currency=filters.currency,
            services=filters.services,
            accounts=filters.accounts,
        )
        year_start = reference_date.replace(month=1, day=1)
        year_filters = QueryFilters(
            cloud=filters.cloud,
            start=year_start,
            end=reference_date,
            currency=filters.currency,
            services=filters.services,
            accounts=filters.accounts,
        )

        budget_month = self.targets.monthly_target(
            cloud=filters.cloud,
            month_date=month_start,
            currency=filters.currency,
        )
        budget_year = self.targets.yearly_target(
            cloud=filters.cloud,
            year=reference_date.year,
            currency=filters.currency,
        )

        usd_rate = None
        if self.currency_repo is not None:
            usd_rate = self.currency_repo.get_brl_per_usd(filters.end)
        if usd_rate is None:
            usd_rate = self.fact_repo.infer_brl_per_usd(
                QueryFilters(
                    cloud=filters.cloud,
                    start=year_start,
                    end=reference_date,
                    currency=filters.currency,
                    services=filters.services,
                    accounts=filters.accounts,
                )
            )
        if usd_rate is None:
            usd_rate = settings.usd_rate_fallback

        return SummaryV2Response(
            totalWeek=week_total,
            deltaWeek=delta_pct,
            avgDaily=avg_daily,
            peakDay=peak_day,
            monthTotal=self.fact_repo.total(month_filters),
            yearTotal=self.fact_repo.total(year_filters),
            budgetMonth=budget_month,
            budgetYear=budget_year,
            usdRate=usd_rate,
        )

    def daily_v2(self, filters: QueryFilters, top_n: int) -> list[DailyItem]:
        rows = self.fact_repo.daily_with_service_breakdown(filters, top_n=top_n)
        return [DailyItem(**row) for row in rows]

    def top_services_v2(self, filters: QueryFilters, limit: int) -> list[dict]:
        current_rows = self.fact_repo.daily_with_service_breakdown(filters, top_n=limit)
        current_totals: dict[str, float] = {}
        for row in current_rows:
            for service_name, amount in (row.get("byService") or {}).items():
                current_totals[service_name] = current_totals.get(service_name, 0.0) + float(amount)

        range_days = max((filters.end - filters.start).days + 1, 1)
        prev_filters = QueryFilters(
            cloud=filters.cloud,
            start=filters.start - timedelta(days=range_days),
            end=filters.start - timedelta(days=1),
            currency=filters.currency,
            services=filters.services,
            accounts=filters.accounts,
        )
        prev_rows = self.fact_repo.daily_with_service_breakdown(prev_filters, top_n=limit)
        prev_totals: dict[str, float] = {}
        for row in prev_rows:
            for service_name, amount in (row.get("byService") or {}).items():
                prev_totals[service_name] = prev_totals.get(service_name, 0.0) + float(amount)

        period_total = float(sum(current_totals.values()) or 0.0)
        ordered_services = sorted(
            [name for name in current_totals.keys() if name != "Others"],
            key=lambda name: current_totals.get(name, 0.0),
            reverse=True,
        )
        if "Others" in current_totals:
            ordered_services.append("Others")

        items: list[dict] = []
        for service_name in ordered_services:
            total = current_totals.get(service_name, 0.0)
            previous = prev_totals.get(service_name, 0.0)
            delta = total - previous
            delta_pct = (delta / previous * 100.0) if previous > 0 else 0.0
            share_pct = (total / period_total * 100.0) if period_total > 0 else 0.0
            items.append(
                {
                    "serviceName": service_name,
                    "total": total,
                    "sharePct": share_pct,
                    "delta": delta,
                    "deltaPct": delta_pct,
                }
            )
        return items[:limit]

    def top_accounts_v2(self, filters: QueryFilters, limit: int) -> list[dict]:
        return self.fact_repo.top_accounts_with_delta(filters, limit)

    def filters_v2(self, cloud: str, month: str | None = None) -> dict[str, list[str]]:
        return self.fact_repo.filter_lists(cloud=cloud, month=month)
