from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class CloudFilter(StrEnum):
    AWS = "aws"
    AZURE = "azure"
    OCI = "oci"
    ALL = "all"


class DateRange(BaseModel):
    start: date
    end: date


class FilterQuery(BaseModel):
    cloud: CloudFilter = CloudFilter.ALL
    start: date
    end: date
    scope_key: str | None = None
    service_key: str | None = None


class TopItem(BaseModel):
    key: str
    name: str
    total: float = Field(default=0.0)
