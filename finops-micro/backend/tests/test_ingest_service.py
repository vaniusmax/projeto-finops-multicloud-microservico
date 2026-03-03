from __future__ import annotations

from datetime import date
from decimal import Decimal

from finops_api.providers.common.types import CanonicalCostRow
from finops_api.services.ingest_service import IngestService


def test_coalesce_rows_sums_duplicate_natural_keys_and_preserves_skus() -> None:
    service = IngestService(db=None)  # type: ignore[arg-type]

    rows = [
        CanonicalCostRow(
            cloud="oci",
            usage_date=date(2026, 2, 23),
            scope_key="OCVS_CORP",
            scope_name="OCVS_CORP",
            service_key="VMware",
            service_name="VMware",
            region_key="sa-saopaulo-1",
            region_name="sa-saopaulo-1",
            currency_code="BRL",
            amount=Decimal("3627.761472"),
            amount_brl=Decimal("3627.761472"),
            source_ref="oci_usage_cli",
            metadata_json={"sku_name": "Base"},
        ),
        CanonicalCostRow(
            cloud="oci",
            usage_date=date(2026, 2, 23),
            scope_key="OCVS_CORP",
            scope_name="OCVS_CORP",
            service_key="VMware",
            service_name="VMware",
            region_key="sa-saopaulo-1",
            region_name="sa-saopaulo-1",
            currency_code="BRL",
            amount=Decimal("3838.793472"),
            amount_brl=Decimal("3838.793472"),
            source_ref="oci_usage_cli",
            metadata_json={"sku_name": "Expansion"},
        ),
    ]

    coalesced = service._coalesce_rows(rows)  # noqa: SLF001

    assert len(coalesced) == 1
    assert coalesced[0].amount == Decimal("7466.554944")
    assert coalesced[0].amount_brl == Decimal("7466.554944")
    assert coalesced[0].metadata_json["sku_names"] == ["Base", "Expansion"]
    assert coalesced[0].metadata_json["sku_count"] == 2
    assert coalesced[0].metadata_json["merged_records"] == 2


def test_coalesce_rows_keeps_distinct_services_separate() -> None:
    service = IngestService(db=None)  # type: ignore[arg-type]

    rows = [
        CanonicalCostRow(
            cloud="oci",
            usage_date=date(2026, 2, 23),
            scope_key="OCVS_CORP",
            scope_name="OCVS_CORP",
            service_key="VMware",
            service_name="VMware",
            region_key="sa-saopaulo-1",
            region_name="sa-saopaulo-1",
            currency_code="BRL",
            amount=Decimal("10"),
            amount_brl=Decimal("10"),
            source_ref="oci_usage_cli",
            metadata_json={"sku_name": "Base"},
        ),
        CanonicalCostRow(
            cloud="oci",
            usage_date=date(2026, 2, 23),
            scope_key="OCVS_CORP",
            scope_name="OCVS_CORP",
            service_key="Block Storage",
            service_name="Block Storage",
            region_key="sa-saopaulo-1",
            region_name="sa-saopaulo-1",
            currency_code="BRL",
            amount=Decimal("20"),
            amount_brl=Decimal("20"),
            source_ref="oci_usage_cli",
            metadata_json={"sku_name": "Volume"},
        ),
    ]

    coalesced = service._coalesce_rows(rows)  # noqa: SLF001

    assert len(coalesced) == 2
