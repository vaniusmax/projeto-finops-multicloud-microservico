from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from finops_api.providers.common.types import CanonicalCostRow


@dataclass(frozen=True)
class OciCliSettings:
    tenant_id: str
    cli_path: str = "oci"
    profile: str = "DEFAULT"
    region: str = "sa-saopaulo-1"
    granularity: str = "DAILY"
    query_type: str = "COST"


class OciCliClient:
    def __init__(self, settings: OciCliSettings) -> None:
        if not settings.tenant_id:
            raise ValueError("tenant_id é obrigatório para ingestão OCI")
        self.settings = settings

    def fetch_daily_costs(self, start: date, end: date) -> list[CanonicalCostRow]:
        command = [
            self.settings.cli_path,
            "usage-api",
            "usage-summary",
            "request-summarized-usages",
            "--profile",
            self.settings.profile,
            "--region",
            self.settings.region,
            "--tenant-id",
            self.settings.tenant_id,
            "--time-usage-started",
            self._iso_z(start),
            "--time-usage-ended",
            self._iso_z(end + timedelta(days=1)),
            "--granularity",
            self.settings.granularity,
            "--query-type",
            self.settings.query_type,
            "--group-by",
            json.dumps(["compartmentName", "service", "skuName"]),
            "--compartment-depth",
            "1",
            "--output",
            "json",
        ]
        env = os.environ.copy()
        env.setdefault("SUPPRESS_LABEL_WARNING", "True")
        result = subprocess.run(command, check=False, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            error_text = result.stderr.strip() or result.stdout.strip() or "Falha OCI Usage API"
            raise RuntimeError(f"Falha no OCI CLI: {error_text}")
        return self._parse(json.loads(result.stdout))

    def _parse(self, payload: dict[str, Any]) -> list[CanonicalCostRow]:
        rows: list[CanonicalCostRow] = []
        for item in ((payload.get("data") or {}).get("items") or []):
            usage_text = str(item.get("time-usage-started", "")).replace("Z", "+00:00")
            if not usage_text:
                continue
            usage_date = datetime.fromisoformat(usage_text).date()
            service = str(item.get("service") or "Outros")
            compartment = str(item.get("compartment-name") or "Sem compartment")
            sku_name = str(item.get("sku-name") or "Outros")
            currency = str(
                item.get("currency")
                or item.get("currency-code")
                or item.get("currencyCode")
                or "BRL"
            ).strip().upper() or "BRL"
            amount = Decimal(str(item.get("computed-amount") or "0"))

            rows.append(
                CanonicalCostRow(
                    cloud="oci",
                    usage_date=usage_date,
                    scope_key=compartment,
                    scope_name=compartment,
                    service_key=service,
                    service_name=service,
                    region_key=self.settings.region,
                    region_name=self.settings.region,
                    currency_code=currency,
                    amount=amount,
                    amount_brl=amount if currency.upper() == "BRL" else None,
                    source_ref="oci_usage_cli",
                    metadata_json={"sku_name": sku_name},
                )
            )
        return rows

    @staticmethod
    def _iso_z(day: date) -> str:
        dt = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
