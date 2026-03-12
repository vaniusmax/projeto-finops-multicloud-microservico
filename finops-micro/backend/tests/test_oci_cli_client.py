from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

from finops_api.providers.oci.cli_client import OciCliClient, OciCliSettings


def test_fetch_daily_costs_uses_default_compartment_depth(monkeypatch) -> None:
    captured: dict[str, list[str]] = {}

    def fake_run(command, check, capture_output, text, env):  # noqa: ANN001
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout=json.dumps({"data": {"items": []}}), stderr="")

    monkeypatch.setattr("finops_api.providers.oci.cli_client.subprocess.run", fake_run)

    client = OciCliClient(
        OciCliSettings(
            tenant_id="ocid1.tenancy.oc1..example",
        )
    )
    client.fetch_daily_costs(start=date(2026, 3, 2), end=date(2026, 3, 8))

    command = captured["command"]
    assert "--compartment-depth" in command
    depth_index = command.index("--compartment-depth")
    assert command[depth_index + 1] == "6"


def test_fetch_daily_costs_applies_compartment_depth_when_configured(monkeypatch) -> None:
    captured: dict[str, list[str]] = {}

    def fake_run(command, check, capture_output, text, env):  # noqa: ANN001
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout=json.dumps({"data": {"items": []}}), stderr="")

    monkeypatch.setattr("finops_api.providers.oci.cli_client.subprocess.run", fake_run)

    client = OciCliClient(
        OciCliSettings(
            tenant_id="ocid1.tenancy.oc1..example",
            compartment_depth=6,
        )
    )
    client.fetch_daily_costs(start=date(2026, 3, 2), end=date(2026, 3, 8))

    command = captured["command"]
    assert "--compartment-depth" in command
    depth_index = command.index("--compartment-depth")
    assert command[depth_index + 1] == "6"
