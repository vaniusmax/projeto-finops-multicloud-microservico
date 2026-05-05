from __future__ import annotations

from datetime import date

from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.services.analytics_service import AnalyticsService


class FixedDate(date):
    @classmethod
    def today(cls) -> "FixedDate":
        return cls(2026, 5, 5)


class FakeFactRepo:
    def __init__(self) -> None:
        self.total_calls: list[QueryFilters] = []

    def total(self, filters: QueryFilters) -> float:
        self.total_calls.append(filters)
        key = (filters.start, filters.end)
        totals = {
            (date(2026, 4, 9), date(2026, 4, 15)): 21280.0,
            (date(2026, 4, 2), date(2026, 4, 8)): 14508.0,
            (date(2026, 5, 1), date(2026, 5, 5)): 17010.0,
            (date(2026, 1, 1), date(2026, 4, 15)): 448970.0,
        }
        return totals.get(key, 0.0)

    def timeseries(self, filters: QueryFilters) -> list[dict]:
        return [
            {"date": filters.start, "total": 1200.0},
            {"date": filters.end, "total": 3500.0},
        ]

    def infer_brl_per_usd(self, filters: QueryFilters) -> float:
        return 5.1394


class FakeTargets:
    def __init__(self) -> None:
        self.monthly_calls: list[tuple[str, date, str]] = []
        self.yearly_calls: list[tuple[str, int, str]] = []

    def monthly_target(self, cloud: str, month_date: date, currency: str) -> float:
        self.monthly_calls.append((cloud, month_date, currency))
        return 138531.58

    def yearly_target(self, cloud: str, year: int, currency: str) -> float:
        self.yearly_calls.append((cloud, year, currency))
        return 1662378.96


def test_summary_v2_uses_current_month_for_month_cards(monkeypatch) -> None:
    monkeypatch.setattr("finops_api.services.analytics_service.date", FixedDate)
    repo = FakeFactRepo()
    targets = FakeTargets()
    service = AnalyticsService(repo, currency_repo=None, targets=targets)

    response = service.summary_v2(
        QueryFilters(
            cloud="aws",
            start=date(2026, 4, 9),
            end=date(2026, 4, 15),
            currency="BRL",
            tenant_key="default",
        )
    )

    assert response.monthTotal == 17010.0
    assert response.budgetMonth == 138531.58
    assert targets.monthly_calls == [("aws", date(2026, 5, 1), "BRL")]
    assert any(call.start == date(2026, 5, 1) and call.end == date(2026, 5, 5) for call in repo.total_calls)
