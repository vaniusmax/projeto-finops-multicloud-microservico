from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class FilterOption(BaseModel):
    key: str
    name: str


class CloudScopes(BaseModel):
    cloud: str
    scopes: list[FilterOption]


class AvailableRange(BaseModel):
    min_date: date | None = None
    max_date: date | None = None


class FiltersResponse(BaseModel):
    clouds: list[str]
    scopes_by_cloud: list[CloudScopes]
    services_top: list[FilterOption]
    regions_top: list[FilterOption]
    available_range: AvailableRange
