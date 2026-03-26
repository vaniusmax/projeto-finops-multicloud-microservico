from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from finops_api.providers.common import run_cli_with_retry
from finops_api.providers.common.types import CanonicalCostRow


@dataclass(frozen=True)
class OciCliSettings:
    tenant_id: str
    cli_path: str = "oci"
    profile: str = "DEFAULT"
    region: str = "sa-saopaulo-1"
    granularity: str = "DAILY"
    query_type: str = "COST"
    compartment_depth: int = 6
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 5.0


class OciCliClient:
    def __init__(self, provider_settings: OciCliSettings) -> None:
        if not provider_settings.tenant_id:
            raise ValueError("tenant_id é obrigatório para ingestão OCI")
        self.settings = provider_settings

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
            json.dumps(["compartmentName", "service", "skuName", "region"]),
            "--compartment-depth",
            str(self.settings.compartment_depth),
            "--output",
            "json",
        ]
        env = os.environ.copy()
        env.setdefault("SUPPRESS_LABEL_WARNING", "True")
        stdout = run_cli_with_retry(
            command,
            timeout=self.settings.timeout,
            max_attempts=self.settings.retry_attempts,
            retry_delay=self.settings.retry_delay,
            env=env,
            label="OCI Usage",
        )
        return self._parse(json.loads(stdout))

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
            item_region = str(item.get("region") or self.settings.region)
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
                    region_key=item_region,
                    region_name=item_region,
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
