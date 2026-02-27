from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from finops_api.providers.common.types import CanonicalCostRow


@dataclass(frozen=True)
class AwsCliSettings:
    cli_path: str = "aws"
    profile: str | None = None
    metric: str = "UnblendedCost"


class AwsCliClient:
    def __init__(self, settings: AwsCliSettings) -> None:
        self.settings = settings

    def fetch_daily_costs(self, start: date, end: date) -> list[CanonicalCostRow]:
        service_rows = self._fetch_grouped_rows(start, end, group_by_keys=["SERVICE"])
        account_rows = self._fetch_grouped_rows(start, end, group_by_keys=["LINKED_ACCOUNT"])
        return service_rows + account_rows

    def _fetch_grouped_rows(self, start: date, end: date, group_by_keys: list[str]) -> list[CanonicalCostRow]:
        end_exclusive = end + timedelta(days=1)
        all_results: list[dict[str, Any]] = []
        group_definitions: list[dict[str, Any]] = []
        next_token: str | None = None

        while True:
            payload = self._run_ce_query(start, end_exclusive, next_token, group_by_keys=group_by_keys)
            all_results.extend(payload.get("ResultsByTime", []))
            if not group_definitions:
                group_definitions = payload.get("GroupDefinitions", [])
            next_token = payload.get("NextPageToken")
            if not next_token:
                break

        if group_by_keys == ["SERVICE"]:
            return self._parse_service_results(all_results, group_definitions)
        return self._parse_account_results(all_results, group_definitions)

    def _run_ce_query(
        self,
        start: date,
        end_exclusive: date,
        next_token: str | None,
        group_by_keys: list[str],
    ) -> dict[str, Any]:
        command = [
            self.settings.cli_path,
            "ce",
            "get-cost-and-usage",
            "--time-period",
            f"Start={start.isoformat()},End={end_exclusive.isoformat()}",
            "--granularity",
            "DAILY",
            "--metrics",
            self.settings.metric,
            "--output",
            "json",
        ]
        for key in group_by_keys:
            command.extend(["--group-by", f"Type=DIMENSION,Key={key}"])
        if self.settings.profile:
            command.extend(["--profile", self.settings.profile])
        if next_token:
            command.extend(["--next-page-token", next_token])

        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            error_text = completed.stderr.strip() or completed.stdout.strip() or "Falha AWS CE"
            raise RuntimeError(f"Falha no AWS CLI: {error_text}")
        return json.loads(completed.stdout)

    def _parse_service_results(self, results: list[dict[str, Any]], group_definitions: list[dict[str, Any]]) -> list[CanonicalCostRow]:
        positions = {definition.get("Key"): idx for idx, definition in enumerate(group_definitions) if definition.get("Key")}
        service_idx = positions.get("SERVICE", 0)

        rows: list[CanonicalCostRow] = []
        for result in results:
            usage_date_raw = (result.get("TimePeriod") or {}).get("Start")
            if not usage_date_raw:
                continue
            usage_day = date.fromisoformat(str(usage_date_raw))

            for group in result.get("Groups", []):
                keys = group.get("Keys", [])
                if not keys:
                    continue
                service = str(keys[service_idx]) if service_idx < len(keys) else "Outros"
                metrics = group.get("Metrics", {})
                metric_data = metrics.get(self.settings.metric) or next(iter(metrics.values()), {})
                amount = Decimal(str(metric_data.get("Amount") or "0"))

                rows.append(
                    CanonicalCostRow(
                        cloud="aws",
                        usage_date=usage_day,
                        scope_key="__ALL__",
                        scope_name="__ALL__",
                        service_key=service,
                        service_name=service,
                        region_key="global",
                        region_name="Global",
                        currency_code="USD",
                        amount=amount,
                        amount_brl=None,
                        source_ref="aws_ce_service_cli",
                        metadata_json={"metric": self.settings.metric, "source": "ce_service"},
                    )
                )
        return rows

    def _parse_account_results(self, results: list[dict[str, Any]], group_definitions: list[dict[str, Any]]) -> list[CanonicalCostRow]:
        positions = {definition.get("Key"): idx for idx, definition in enumerate(group_definitions) if definition.get("Key")}
        account_idx = positions.get("LINKED_ACCOUNT", 0)

        rows: list[CanonicalCostRow] = []
        for result in results:
            usage_date_raw = (result.get("TimePeriod") or {}).get("Start")
            if not usage_date_raw:
                continue
            usage_day = date.fromisoformat(str(usage_date_raw))

            for group in result.get("Groups", []):
                keys = group.get("Keys", [])
                if not keys:
                    continue
                account = str(keys[account_idx]) if account_idx < len(keys) else "__ALL__"
                metrics = group.get("Metrics", {})
                metric_data = metrics.get(self.settings.metric) or next(iter(metrics.values()), {})
                amount = Decimal(str(metric_data.get("Amount") or "0"))

                rows.append(
                    CanonicalCostRow(
                        cloud="aws",
                        usage_date=usage_day,
                        scope_key=account,
                        scope_name=account,
                        service_key="__ALL__",
                        service_name="__ALL__",
                        region_key="global",
                        region_name="Global",
                        currency_code="USD",
                        amount=amount,
                        amount_brl=None,
                        source_ref="aws_ce_account_cli",
                        metadata_json={"metric": self.settings.metric},
                    )
                )
        return rows
