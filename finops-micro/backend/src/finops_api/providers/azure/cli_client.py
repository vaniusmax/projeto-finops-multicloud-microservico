from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from finops_api.providers.common import run_cli_with_retry
from finops_api.providers.common.types import CanonicalCostRow


@dataclass(frozen=True)
class AzureCliSettings:
    management_group_id: str
    api_version: str = "2023-11-01"
    cli_path: str = "az"
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 5.0


class AzureCliClient:
    def __init__(self, provider_settings: AzureCliSettings) -> None:
        if not provider_settings.management_group_id:
            raise ValueError("management_group_id é obrigatório para ingestão Azure")
        self.settings = provider_settings
        self.endpoint = (
            "https://management.azure.com/providers/Microsoft.Management"
            f"/managementGroups/{provider_settings.management_group_id}"
            "/providers/Microsoft.CostManagement/query"
            f"?api-version={provider_settings.api_version}"
        )

    def fetch_daily_costs(self, start: date, end: date) -> list[CanonicalCostRow]:
        payload = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {"from": start.isoformat(), "to": end.isoformat()},
            "dataset": {
                "granularity": "Daily",
                "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                "grouping": [
                    {"type": "Dimension", "name": "SubscriptionName"},
                    {"type": "Dimension", "name": "ServiceName"},
                    {"type": "Dimension", "name": "ResourceLocation"},
                ],
            },
        }

        rows: list[CanonicalCostRow] = []
        next_uri = self.endpoint
        while next_uri:
            response = self._run_query(next_uri, payload)
            rows.extend(self._parse(response))
            next_uri = (response.get("properties") or {}).get("nextLink")
        return rows

    def _run_query(self, uri: str, payload: dict[str, Any]) -> dict[str, Any]:
        command = [
            self.settings.cli_path,
            "rest",
            "--method",
            "post",
            "--uri",
            uri,
            "--body",
            json.dumps(payload),
            "-o",
            "json",
        ]
        stdout = run_cli_with_retry(
            command,
            timeout=self.settings.timeout,
            max_attempts=self.settings.retry_attempts,
            retry_delay=self.settings.retry_delay,
            label="Azure Cost",
        )
        return json.loads(stdout)

    def _parse(self, payload: dict[str, Any]) -> list[CanonicalCostRow]:
        props = payload.get("properties", {})
        raw_rows = props.get("rows") or []
        columns = [c.get("name") for c in (props.get("columns") or [])]
        default_currency = str(props.get("currency") or "BRL").strip().upper() or "BRL"

        parsed: list[CanonicalCostRow] = []
        for raw in raw_rows:
            item = dict(zip(columns, raw))
            usage_date = self._parse_usage_date(item.get("UsageDate"))
            if usage_date is None:
                continue

            service = str(item.get("ServiceName") or "Outros")
            subscription = str(item.get("SubscriptionName") or "Outros")
            region = str(item.get("ResourceLocation") or "global")
            amount = Decimal(str(item.get("PreTaxCost") or "0"))
            currency = str(
                item.get("Currency")
                or item.get("BillingCurrency")
                or default_currency
            ).strip().upper() or default_currency

            parsed.append(
                CanonicalCostRow(
                    cloud="azure",
                    usage_date=usage_date,
                    scope_key=subscription,
                    scope_name=subscription,
                    service_key=service,
                    service_name=service,
                    region_key=region,
                    region_name=region,
                    currency_code=currency,
                    amount=amount,
                    amount_brl=amount if currency.upper() == "BRL" else None,
                    source_ref="azure_cost_cli",
                    metadata_json={"source": "az rest"},
                )
            )
        return parsed

    @staticmethod
    def _parse_usage_date(value: Any) -> date | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.isdigit() and len(text) == 8:
            try:
                return datetime.strptime(text, "%Y%m%d").date()
            except ValueError:
                return None
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            return None
