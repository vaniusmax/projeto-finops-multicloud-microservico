from __future__ import annotations

from pydantic import BaseModel

from finops_api.schemas.common import TopItem


class DeltaInfo(BaseModel):
    absolute: float
    percent: float | None


class SummaryResponse(BaseModel):
    total_current: float
    total_previous: float
    delta: DeltaInfo
    top_services: list[TopItem]
    top_scopes: list[TopItem]
