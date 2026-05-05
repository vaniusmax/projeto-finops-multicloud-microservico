from __future__ import annotations

import json
from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from finops_api.core.config import settings

FIXED_MONTHLY_TARGETS_BRL_BY_CLOUD = {
    "aws": 138_531.58,
    "azure": 231_437.64,
    "oci": 331_894.50,
}


@dataclass(frozen=True)
class TargetDefaults:
    monthly_brl: float
    monthly_usd: float
    weekly_brl: float
    weekly_usd: float


class TargetsService:
    def __init__(self) -> None:
        self.defaults = TargetDefaults(
            monthly_brl=settings.target_monthly_brl,
            monthly_usd=settings.target_monthly_usd,
            weekly_brl=settings.target_weekly_brl,
            weekly_usd=settings.target_weekly_usd,
        )
        self.monthly_targets_by_cloud = self._parse_monthly_targets(settings.monthly_targets_json)

    @staticmethod
    def _default_monthly_target(currency: str, cloud: str) -> float:
        currency_key = currency.upper()
        if currency_key == "BRL":
            fixed = FIXED_MONTHLY_TARGETS_BRL_BY_CLOUD.get((cloud or "all").lower())
            if fixed and fixed > 0:
                return fixed
            configured = float(settings.target_monthly_brl or 0.0)
            return configured if configured > 0 else 0.0

        configured_usd = float(settings.target_monthly_usd or 0.0)
        return configured_usd if configured_usd > 0 else 0.0

    @staticmethod
    def _parse_monthly_targets(raw: str) -> dict[str, dict[tuple[int, int], float]]:
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, dict):
            return {}
        parsed: dict[str, dict[tuple[int, int], float]] = {}
        for cloud, values in payload.items():
            if not isinstance(values, dict):
                continue
            cloud_key = str(cloud).strip().lower()
            month_map: dict[tuple[int, int], float] = {}
            for key, value in values.items():
                try:
                    year_str, month_str = str(key).split("-")
                    month_map[(int(year_str), int(month_str))] = float(value)
                except (TypeError, ValueError):
                    continue
            if month_map:
                parsed[cloud_key] = month_map
        return parsed

    def monthly_target(self, cloud: str, month_date: date, currency: str) -> float:
        currency_key = currency.upper()
        cloud_key = (cloud or "all").lower()
        default_target = self._default_monthly_target(currency=currency_key, cloud=cloud_key)
        if currency_key != "BRL":
            return default_target

        cloud_map = self.monthly_targets_by_cloud.get(cloud_key) or self.monthly_targets_by_cloud.get("all")
        if not cloud_map:
            return default_target
        configured_target = cloud_map.get((month_date.year, month_date.month))
        if configured_target is None:
            return default_target
        configured_target = float(configured_target)
        return configured_target if configured_target > 0 else default_target

    def yearly_target(self, cloud: str, year: int, currency: str) -> float:
        total = 0.0
        for month in range(1, 13):
            month_date = date(year, month, 1)
            total += self.monthly_target(cloud=cloud, month_date=month_date, currency=currency)
        return total

    def weekly_target(self, cloud: str, start: date, end: date, currency: str) -> float:
        if start > end:
            start, end = end, start
        period_days = (end - start).days + 1
        if period_days <= 0:
            return 0.0

        acc_target = 0.0
        cursor = start.replace(day=1)
        while cursor <= end:
            month_start = cursor
            _, days_in_month = monthrange(month_start.year, month_start.month)
            month_end = month_start.replace(day=days_in_month)
            overlap_start = max(start, month_start)
            overlap_end = min(end, month_end)
            if overlap_end >= overlap_start:
                overlap_days = (overlap_end - overlap_start).days + 1
                month_target = self.monthly_target(cloud=cloud, month_date=month_start, currency=currency)
                if days_in_month > 0 and month_target > 0:
                    acc_target += month_target * (overlap_days / days_in_month)
            if month_start.month == 12:
                cursor = month_start.replace(year=month_start.year + 1, month=1, day=1)
            else:
                cursor = month_start.replace(month=month_start.month + 1, day=1)

        if acc_target > 0:
            return acc_target

        fallback_weekly = self.defaults.weekly_brl if currency.upper() == "BRL" else self.defaults.weekly_usd
        return fallback_weekly * (period_days / 7)
