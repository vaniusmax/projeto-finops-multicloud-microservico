from __future__ import annotations

from datetime import date

from finops_api.core.config import settings
from finops_api.services.targets_service import TargetsService


def test_monthly_target_uses_fixed_cloud_values_when_env_is_zero(monkeypatch) -> None:
    monkeypatch.setattr(settings, "target_monthly_brl", 0.0)
    monkeypatch.setattr(settings, "target_monthly_usd", 0.0)
    monkeypatch.setattr(settings, "monthly_targets_json", "")

    service = TargetsService()

    assert service.monthly_target("aws", date(2026, 5, 1), "BRL") == 138531.58
    assert service.monthly_target("azure", date(2026, 5, 1), "BRL") == 231437.64
    assert service.monthly_target("oci", date(2026, 5, 1), "BRL") == 331894.50


def test_monthly_target_prefers_positive_json_override_and_ignores_zero_override(monkeypatch) -> None:
    monkeypatch.setattr(settings, "target_monthly_brl", 0.0)
    monkeypatch.setattr(settings, "monthly_targets_json", '{"aws":{"2026-05":140000},"azure":{"2026-05":0}}')

    service = TargetsService()

    assert service.monthly_target("aws", date(2026, 5, 1), "BRL") == 140000.0
    assert service.monthly_target("azure", date(2026, 5, 1), "BRL") == 231437.64
