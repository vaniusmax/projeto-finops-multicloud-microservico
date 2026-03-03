from __future__ import annotations

from datetime import date
from uuid import uuid4

from finops_api.repositories.fact_cost_repo import FactCostRepository, QueryFilters


class FakeScalarResult:
    def __init__(self, scalar=None, row=None) -> None:
        self.scalar = scalar
        self.row = row

    def scalar_one(self):
        return self.scalar

    def one(self):
        return self.row


class FakeSession:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def execute(self, stmt):
        self.statements.append(str(stmt))
        if "sum_brl" in str(stmt):
            row = type("Row", (), {"sum_brl": 0.0, "sum_usd": 0.0})()
            return FakeScalarResult(row=row)
        return FakeScalarResult(scalar=0)


def test_total_filters_by_tenant_id() -> None:
    session = FakeSession()
    repo = FactCostRepository(session)
    tenant_id = uuid4()

    repo.total(
        QueryFilters(
            cloud="oci",
            tenant_id=tenant_id,
            tenant_key="OCI-TENANT-OCVS",
            start=date(2026, 2, 1),
            end=date(2026, 2, 28),
            currency="BRL",
        )
    )

    assert any("fact_cost_daily.tenant_id" in stmt for stmt in session.statements)
