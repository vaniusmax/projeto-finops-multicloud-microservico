from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CanonicalCostRow:
    cloud: str
    usage_date: date
    scope_key: str
    scope_name: str
    service_key: str
    service_name: str
    region_key: str
    region_name: str
    currency_code: str
    amount: Decimal
    amount_brl: Decimal | None = None
    source_ref: str = "cli_ingest"
    metadata_json: dict = field(default_factory=dict)
