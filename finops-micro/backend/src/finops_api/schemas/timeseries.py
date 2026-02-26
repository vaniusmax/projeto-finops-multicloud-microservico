from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class Granularity(StrEnum):
    DAILY = "daily"


class TimeseriesPoint(BaseModel):
    date: date
    total: float


class TimeseriesResponse(BaseModel):
    granularity: str
    points: list[TimeseriesPoint]
