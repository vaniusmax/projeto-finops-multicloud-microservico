from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from finops_api.api.v1.deps import get_analytics_service
from finops_api.db.session import get_db
from finops_api.repositories.fact_cost_repo import QueryFilters
from finops_api.schemas.finops import (
    AiInsightRequest,
    AiInsightResponse,
    DailyItem,
    FiltersV2Response,
    RankedItemV2,
    ReingestRequest,
    ReingestResponse,
    ReingestResult,
    SummaryV2Response,
)
from finops_api.services.analytics_service import AnalyticsService
from finops_api.services.auto_ingest_service import AutoIngestService
from finops_api.services.ingest_service import run_ingest_job

router = APIRouter(prefix="/finops", tags=["finops-v2"])


def parse_finops_filters(
    cloud: str = Query(default="all", pattern="^(aws|azure|oci|all)$"),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    currency: str = Query(default="BRL", pattern="^(BRL|USD)$"),
    services: list[str] | None = Query(default=None),
    accounts: list[str] | None = Query(default=None),
) -> QueryFilters:
    if from_date > to_date:
        raise ValueError("from deve ser menor ou igual a to")
    return QueryFilters(
        cloud=cloud,
        start=from_date,
        end=to_date,
        currency=currency,
        services=services or None,
        accounts=accounts or None,
    )


def ensure_ingest_v2(filters: QueryFilters = Depends(parse_finops_filters), db: Session = Depends(get_db)) -> QueryFilters:
    AutoIngestService(db).ensure_range(filters.cloud, filters.start, filters.end)
    return filters


def ensure_ingest_v2_refreshable(
    filters: QueryFilters = Depends(parse_finops_filters),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> QueryFilters:
    if refresh:
        providers = ["aws", "azure", "oci"] if filters.cloud == "all" else [filters.cloud]
        for provider in providers:
            run_ingest_job(db, provider=provider, start=filters.start, end=filters.end)
    else:
        AutoIngestService(db).ensure_range(filters.cloud, filters.start, filters.end)
    return filters


def ensure_ingest_v2_summary(
    filters: QueryFilters = Depends(parse_finops_filters),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> QueryFilters:
    reference_date = date.today()
    year_start = reference_date.replace(month=1, day=1)
    if refresh:
        providers = ["aws", "azure", "oci"] if filters.cloud == "all" else [filters.cloud]
        for provider in providers:
            run_ingest_job(db, provider=provider, start=year_start, end=reference_date)
    else:
        AutoIngestService(db).ensure_range(filters.cloud, year_start, reference_date)
    return filters


@router.get("/summary", response_model=SummaryV2Response)
def get_summary_v2(
    filters: QueryFilters = Depends(ensure_ingest_v2_summary),
    service: AnalyticsService = Depends(get_analytics_service),
) -> SummaryV2Response:
    try:
        return service.summary_v2(filters)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/daily", response_model=list[DailyItem])
def get_daily_v2(
    filters: QueryFilters = Depends(ensure_ingest_v2_refreshable),
    top_n: int = Query(default=10, alias="topN", ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[DailyItem]:
    try:
        return service.daily_v2(filters, top_n=top_n)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/top-services", response_model=list[RankedItemV2])
def get_top_services_v2(
    filters: QueryFilters = Depends(ensure_ingest_v2_refreshable),
    top_n: int = Query(default=10, alias="topN", ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[RankedItemV2]:
    try:
        return [RankedItemV2(**item) for item in service.top_services_v2(filters, limit=top_n)]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/top-accounts", response_model=list[RankedItemV2])
def get_top_accounts_v2(
    filters: QueryFilters = Depends(ensure_ingest_v2_refreshable),
    top_n: int = Query(default=10, alias="topN", ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[RankedItemV2]:
    try:
        return [RankedItemV2(**item) for item in service.top_accounts_v2(filters, limit=top_n)]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/filters", response_model=FiltersV2Response)
def get_filters_v2(
    cloud: str = Query(default="all", pattern="^(aws|azure|oci|all)$"),
    month: str | None = Query(default=None),
    service: AnalyticsService = Depends(get_analytics_service),
) -> FiltersV2Response:
    try:
        return FiltersV2Response(**service.filters_v2(cloud=cloud, month=month))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/ai/insights", response_model=AiInsightResponse)
def post_ai_insights_v2(payload: AiInsightRequest) -> AiInsightResponse:
    question = payload.question.strip()
    return AiInsightResponse(
        answerMarkdown=(
            f"Pergunta recebida para {payload.cloud.upper()} ({payload.from_.isoformat()} a {payload.to.isoformat()}): {question}. "
            "Use os destaques do dashboard para validar picos, serviços dominantes e contas com maior participação."
        ),
        highlights=[
            "Verifique o pico diário e correlacione com deploys/cargas sazonais.",
            "Compare top serviços com o período anterior para identificar regressões.",
            "Revise linked accounts com maior share no total semanal.",
        ],
        suggestedActions=[
            "Aplicar rightsizing em compute contínuo.",
            "Validar políticas de retenção/lifecycle para storage.",
            "Avaliar savings plans ou reservas para workloads estáveis.",
        ],
    )


@router.post("/reingest", response_model=ReingestResponse)
def post_reingest(payload: ReingestRequest, db: Session = Depends(get_db)) -> ReingestResponse:
    if payload.from_ > payload.to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="from deve ser menor ou igual a to")
    cloud = payload.cloud.lower().strip()
    if cloud not in {"aws", "azure", "oci", "all"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cloud inválida")

    providers = ["aws", "azure", "oci"] if cloud == "all" else [cloud]
    results: list[ReingestResult] = []
    for provider in providers:
        result = run_ingest_job(db, provider=provider, start=payload.from_, end=payload.to)
        results.append(ReingestResult(**result))
    return ReingestResponse(results=results)
