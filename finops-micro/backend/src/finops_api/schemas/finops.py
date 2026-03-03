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


class TenantOption(BaseModel):
    tenantKey: str
    tenantName: str
    cloud: str


class AiInsightRequest(BaseModel):
    cloud: str
    tenant_key: str | None = None
    from_: date = Field(alias="from")
    to: date
    currency: str
    question: str
    filters: dict[str, list[str]] | None = None


class AiInsightResponse(BaseModel):
    answerMarkdown: str
    highlights: list[str]
    suggestedActions: list[str]


class AnalyticsInsightRequest(BaseModel):
    cloud: str
    tenant_key: str | None = None
    from_: date = Field(alias="from")
    to: date
    currency: str
    topN: int = 10
    services: list[str] | None = None
    accounts: list[str] | None = None


class AnalyticsInsightEvidence(BaseModel):
    topServices: list[str] = Field(default_factory=list)
    topAccounts: list[str] = Field(default_factory=list)
    peakDay: date | None = None
    totalPeriod: float
    deltaPeriodPct: float


class AnalyticsInsightAction(BaseModel):
    title: str
    owner: str
    priority: str
    rationale: str


class AnalyticsInsightResponse(BaseModel):
    mode: str
    summary: str
    drivers: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    actions: list[AnalyticsInsightAction] = Field(default_factory=list)
    suggestedQuestions: list[str] = Field(default_factory=list)
    evidence: AnalyticsInsightEvidence


class CostExplorerSnapshotKpi(BaseModel):
    label: str
    value: float
    sharePct: float
    deltaPct: float


class CostExplorerSnapshotResponse(BaseModel):
    totalPeriod: float
    deltaPeriodPct: float
    top1SharePct: float
    top3SharePct: float
    peakDay: PeakDay
    largestService: CostExplorerSnapshotKpi | None = None
    largestAccount: CostExplorerSnapshotKpi | None = None


class CostExplorerBreakdownItem(BaseModel):
    key: str
    label: str
    total: float
    sharePct: float
    delta: float
    deltaPct: float
    contributionPct: float


class CostExplorerTrendItem(BaseModel):
    date: date
    total: float
    selected: float
    others: float


class CostExplorerInsightRequest(BaseModel):
    cloud: str
    tenant_key: str | None = None
    from_: date = Field(alias="from")
    to: date
    currency: str
    topN: int = 10
    groupBy: str = "service"
    selectedItem: str | None = None
    services: list[str] | None = None
    accounts: list[str] | None = None


class CostExplorerInsightEvidence(BaseModel):
    groupBy: str
    selectedItem: str | None = None
    totalPeriod: float
    deltaPeriodPct: float
    peakDay: date | None = None
    topBreakdown: list[str] = Field(default_factory=list)
    topServices: list[str] = Field(default_factory=list)
    topAccounts: list[str] = Field(default_factory=list)


class CostExplorerInsightAction(BaseModel):
    title: str
    owner: str
    priority: str
    rationale: str


class CostExplorerNextDrilldown(BaseModel):
    dimension: str
    value: str
    reason: str


class CostExplorerInsightResponse(BaseModel):
    mode: str
    summary: str
    drivers: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    actions: list[CostExplorerInsightAction] = Field(default_factory=list)
    suggestedQuestions: list[str] = Field(default_factory=list)
    nextDrilldowns: list[CostExplorerNextDrilldown] = Field(default_factory=list)
    evidence: CostExplorerInsightEvidence


class ReingestRequest(BaseModel):
    cloud: str
    tenant_key: str | None = None
    from_: date = Field(alias="from")
    to: date


class ReingestResult(BaseModel):
    provider: str
    rows_received: int
    rows_written: int


class ReingestResponse(BaseModel):
    results: list[ReingestResult]
