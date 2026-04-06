from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.finops import PeakDay, SummaryV2Response
from finops_api.services.ai_mcp_service import AiMcpService


class FakeSqlResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class FakeDB:
    def __init__(self) -> None:
        self.last_stmt = ""

    def execute(self, _stmt, params=None):
        self.last_stmt = str(_stmt)
        cloud = (params or {}).get("cloud", "aws")
        rows_by_cloud = {
            "aws": [
                SimpleNamespace(service_name="EC2", total=580.0),
                SimpleNamespace(service_name="RDS", total=260.0),
            ],
            "azure": [
                SimpleNamespace(service_name="Virtual Machines", total=420.0),
                SimpleNamespace(service_name="Azure SQL Database", total=200.0),
            ],
            "oci": [
                SimpleNamespace(service_name="OCI Compute", total=190.0),
                SimpleNamespace(service_name="OCI Block Volume", total=80.0),
            ],
        }
        return FakeSqlResult(rows_by_cloud.get(cloud, []))


class FakeFactRepo:
    def __init__(self) -> None:
        self.db = FakeDB()

    def has_data_in_range(self, cloud: str, start: date, end: date, tenant_id=None) -> bool:
        del start, end, tenant_id
        return cloud in {"aws", "azure", "oci"}

    def infer_brl_per_usd(self, _filters: QueryFilters) -> float:
        return 5.0


class FakeAnalyticsService:
    def __init__(self) -> None:
        self.fact_repo = FakeFactRepo()

    def summary_v2(self, filters: QueryFilters) -> SummaryV2Response:
        totals = {"aws": 1200.0, "azure": 760.0, "oci": 320.0}
        deltas = {"aws": 11.5, "azure": 4.2, "oci": -2.8}
        total = totals.get(filters.cloud, 0.0)
        return SummaryV2Response(
            totalWeek=total,
            deltaWeek=deltas.get(filters.cloud, 0.0),
            avgDaily=total / 7.0 if total else 0.0,
            peakDay=PeakDay(date=filters.end, amount=total / 4.0 if total else 0.0),
            monthTotal=total * 2.3,
            yearTotal=total * 8.2,
            budgetMonth=None,
            budgetYear=None,
            usdRate=5.0,
        )

    def top_services_v2(self, filters: QueryFilters, limit: int) -> list[dict[str, Any]]:
        del limit
        services = {
            "aws": {"name": "EC2", "total": 580.0, "share": 48.3, "delta": 82.0, "delta_pct": 16.5},
            "azure": {"name": "Virtual Machines", "total": 420.0, "share": 55.2, "delta": 24.0, "delta_pct": 6.1},
            "oci": {"name": "OCI Compute", "total": 190.0, "share": 59.4, "delta": -4.0, "delta_pct": -2.0},
        }
        item = services.get(filters.cloud) or services["aws"]
        return [
            {
                "serviceName": item["name"],
                "total": item["total"],
                "sharePct": item["share"],
                "delta": item["delta"],
                "deltaPct": item["delta_pct"],
            }
        ]


def _patch_tenant_service(monkeypatch) -> None:
    monkeypatch.setattr(
        "finops_api.services.ai_mcp_service.TenantService.get_runtime_configs",
        lambda _self, cloud: [SimpleNamespace(tenant_key=f"{cloud}-tenant")],
    )
    monkeypatch.setattr(
        "finops_api.services.ai_mcp_service.TenantService.resolve_tenant",
        lambda _self, cloud, tenant_key: SimpleNamespace(tenant_id=f"{cloud}-id", tenant_key=tenant_key),
    )


def test_generate_if_applicable_returns_multicloud_comparison(monkeypatch) -> None:
    _patch_tenant_service(monkeypatch)
    service = AiMcpService(FakeAnalyticsService())  # type: ignore[arg-type]
    filters = QueryFilters(
        cloud="aws",
        tenant_key="aws-tenant",
        start=date(2026, 3, 1),
        end=date(2026, 3, 31),
        currency="BRL",
    )

    response = service.generate_if_applicable(
        filters=filters,
        question="Compare AWS vs Azure e OCI no periodo atual",
        top_n=5,
    )

    assert response is not None
    assert "## Comparacao Multi-Cloud (MCP)" in response.answerMarkdown
    assert "AWS" in response.answerMarkdown
    assert "AZURE" in response.answerMarkdown
    assert "Ferramentas MCP usadas" in response.answerMarkdown
    assert len(response.highlights) > 0
    assert len(response.suggestedActions) > 0


def test_generate_if_applicable_returns_sql_response_for_single_cloud(monkeypatch) -> None:
    _patch_tenant_service(monkeypatch)
    service = AiMcpService(FakeAnalyticsService())  # type: ignore[arg-type]
    filters = QueryFilters(
        cloud="aws",
        tenant_key="aws-tenant",
        start=date(2026, 3, 1),
        end=date(2026, 3, 31),
        currency="BRL",
    )

    response = service.generate_if_applicable(
        filters=filters,
        question="Mostre a SQL dos top servicos da AWS neste periodo",
        top_n=5,
    )

    assert response is not None
    assert "## Comparacao Multi-Cloud (MCP)" in response.answerMarkdown
    assert "Ferramentas MCP usadas" in response.answerMarkdown
    assert "AWS" in response.answerMarkdown
    assert "f.cost_date" in service.db.last_stmt
    assert "f.source = 'aws_ce_service_cli'" in service.db.last_stmt
    assert "f.currency = 'USD'" in service.db.last_stmt
    assert "f.usage_date" not in service.db.last_stmt
    assert "f.source_ref" not in service.db.last_stmt
    assert "f.currency_code" not in service.db.last_stmt


def test_generate_if_applicable_ignores_regular_questions(monkeypatch) -> None:
    _patch_tenant_service(monkeypatch)
    service = AiMcpService(FakeAnalyticsService())  # type: ignore[arg-type]
    filters = QueryFilters(
        cloud="aws",
        tenant_key="aws-tenant",
        start=date(2026, 3, 1),
        end=date(2026, 3, 31),
        currency="BRL",
    )

    response = service.generate_if_applicable(
        filters=filters,
        question="Qual foi o pico diario do periodo?",
        top_n=5,
    )

    assert response is None
