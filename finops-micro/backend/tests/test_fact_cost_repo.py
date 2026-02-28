from __future__ import annotations

from datetime import date

from finops_api.repositories.fact_cost_repo import FactCostRepository, QueryFilters


class FakeResult:
    def __init__(self, row) -> None:
        self._row = row

    def one(self):
        return self._row


class FakeSession:
    def __init__(self, row) -> None:
        self.row = row
        self.statements = []

    def execute(self, stmt):
        self.statements.append(str(stmt))
        return FakeResult(self.row)


def test_infer_brl_per_usd_limits_inference_to_usd_rows() -> None:
    session = FakeSession(type("Row", (), {"sum_brl": 0.0, "sum_usd": 0.0})())
    repo = FactCostRepository(session)

    rate = repo.infer_brl_per_usd(
        QueryFilters(
            cloud="azure",
            start=date(2026, 2, 1),
            end=date(2026, 2, 28),
            currency="BRL",
        )
    )

    assert rate is None
    assert any("fact_cost_daily.currency = :currency_1" in stmt for stmt in session.statements)
