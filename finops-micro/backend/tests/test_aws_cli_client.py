from __future__ import annotations

from datetime import date
from decimal import Decimal

from finops_api.providers.aws.cli_client import AwsCliClient, AwsCliSettings


def test_parse_account_results_resolves_aws_account_name() -> None:
    client = AwsCliClient(
        AwsCliSettings(
            account_names={
                "595949041525": "Algar Telecom",
            }
        )
    )

    rows = client._parse_account_results(  # noqa: SLF001
        results=[
            {
                "TimePeriod": {"Start": "2026-02-28"},
                "Groups": [
                    {
                        "Keys": ["595949041525"],
                        "Metrics": {"UnblendedCost": {"Amount": "123.45"}},
                    }
                ],
            }
        ],
        group_definitions=[{"Key": "LINKED_ACCOUNT"}],
    )

    assert len(rows) == 1
    assert rows[0].usage_date == date(2026, 2, 28)
    assert rows[0].scope_key == "595949041525"
    assert rows[0].scope_name == "Algar Telecom"
    assert rows[0].amount == Decimal("123.45")
