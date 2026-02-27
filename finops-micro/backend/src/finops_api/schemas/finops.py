from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PeakDay(BaseModel):
    date: date
    amount: float


class SummaryV2Response(BaseModel):
    totalWeek: float
    deltaWeek: float
    avgDaily: float
    peakDay: PeakDay
    monthTotal: float
    yearTotal: float
    budgetMonth: float | None = None
    budgetYear: float | None = None
    usdRate: float | None = None


class DailyItem(BaseModel):
    date: date
    total: float
    byService: dict[str, float] | None = None


class RankedItemV2(BaseModel):
    serviceName: str | None = None
    linkedAccount: str | None = None
    total: float
    sharePct: float
    delta: float
    deltaPct: float


class FiltersV2Response(BaseModel):
    services: list[str] = Field(default_factory=list)
    accounts: list[str] = Field(default_factory=list)


class AiInsightRequest(BaseModel):
    cloud: str
    from_: date = Field(alias="from")
    to: date
    currency: str
    question: str
    filters: dict[str, list[str]] | None = None


class AiInsightResponse(BaseModel):
    answerMarkdown: str
    highlights: list[str]
    suggestedActions: list[str]


class ReingestRequest(BaseModel):
    cloud: str
    from_: date = Field(alias="from")
    to: date


class ReingestResult(BaseModel):
    provider: str
    rows_received: int
    rows_written: int


class ReingestResponse(BaseModel):
    results: list[ReingestResult]
