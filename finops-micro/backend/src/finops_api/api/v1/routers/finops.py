from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from finops_api.api.v1.deps import get_analytics_service
from finops_api.core.config import settings
from finops_api.db.session import get_db
from finops_api.repositories.fact_cost_repo import FactCostRepository, QueryFilters
from finops_api.schemas.finops import (
    AnalyticsInsightRequest,
    AnalyticsInsightResponse,
    AiInsightRequest,
    AiInsightResponse,
    CostExplorerBreakdownItem,
    CostExplorerInsightRequest,
    CostExplorerInsightResponse,
    CostExplorerSnapshotResponse,
    CostExplorerTrendItem,
    DailyItem,
    FiltersV2Response,
    RankedItemV2,
    ReingestRequest,
    ReingestResponse,
    ReingestResult,
    SummaryV2Response,
)
from finops_api.services.analytics_service import AnalyticsService
from finops_api.services.analytics_insight_service import AnalyticsInsightService
from finops_api.services.auto_ingest_service import AutoIngestService
from finops_api.services.cost_explorer_insight_service import CostExplorerInsightService
from finops_api.services.cost_explorer_service import CostExplorerService
from finops_api.services.currency_rate_sync_service import CurrencyRateSyncService
from finops_api.services.ingest_service import run_ingest_job
from finops_api.services.tenant_service import TenantService

router = APIRouter(prefix="/finops", tags=["finops-v2"])
logger = logging.getLogger(__name__)


def _tenant_keys_for_request(db: Session, cloud: str, requested_tenant_key: str | None) -> list[str | None]:
    if requested_tenant_key:
        return [requested_tenant_key]
    runtime_configs = TenantService(db).get_runtime_configs(cloud)
    if runtime_configs:
        return [config.tenant_key for config in runtime_configs]
    return [None]


def _assert_data_available(db: Session, cloud: str, start: date, end: date, tenant_id=None) -> None:
    repo = FactCostRepository(db)
    providers = ["aws", "azure", "oci"] if cloud == "all" else [cloud]
    missing: list[str] = []

    for provider in providers:
        if provider == "aws":
            has_service_data = repo.has_source_data_in_range(
                cloud="aws",
                start=start,
                end=end,
                source_ref="aws_ce_service_cli",
                tenant_id=tenant_id,
            )
            has_account_data = repo.has_source_data_in_range(
                cloud="aws",
                start=start,
                end=end,
                source_ref="aws_ce_account_cli",
                tenant_id=tenant_id,
            )
            if not (has_service_data and has_account_data):
                missing.append("aws")
            continue
        if not repo.has_data_in_range(provider, start, end, tenant_id=tenant_id):
            missing.append(provider)

    if missing:
        missing_list = ", ".join(sorted(set(missing)))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Sem dados suficientes para o período solicitado. "
                f"Providers sem dados no intervalo: {missing_list}. "
                "Execute refresh/reingest ou ajuste o período."
            ),
        )


def parse_finops_filters(
    cloud: str = Query(default="all", pattern="^(aws|azure|oci|all)$"),
    tenant_key: str | None = Query(default=None, alias="tenant_key"),
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    currency: str = Query(default="BRL", pattern="^(BRL|USD)$"),
    services: list[str] | None = Query(default=None),
    accounts: list[str] | None = Query(default=None),
) -> QueryFilters:
    if from_date > to_date:
        raise ValueError("from deve ser menor ou igual a to")
    range_days = (to_date - from_date).days
    if range_days > settings.ingest_max_range_days:
        raise ValueError(
            f"Intervalo de {range_days} dias excede o maximo permitido de {settings.ingest_max_range_days} dias"
        )
    tenant = TenantService(db=None)  # type: ignore[arg-type]
    tenant.require_tenant_key(cloud, tenant_key)
    return QueryFilters(
        cloud=cloud,
        start=from_date,
        end=to_date,
        currency=currency,
        tenant_key=tenant_key,
        services=services or None,
        accounts=accounts or None,
    )


def ensure_ingest_v2_refreshable(
    filters: QueryFilters = Depends(parse_finops_filters),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> QueryFilters:
    tenant = TenantService(db).resolve_tenant(filters.cloud, filters.tenant_key)
    filters.tenant_id = tenant.tenant_id if tenant else None
    if refresh:
        providers = ["aws", "azure", "oci"] if filters.cloud == "all" else [filters.cloud]
        for provider in providers:
            tenant_keys = _tenant_keys_for_request(db, provider, filters.tenant_key if provider == filters.cloud else None)
            for current_tenant_key in tenant_keys:
                run_ingest_job(db, provider=provider, start=filters.start, end=filters.end, tenant_key=current_tenant_key)
        CurrencyRateSyncService(db).ensure_brl_usd_rate(filters.end)
    else:
        AutoIngestService(db).ensure_range(filters.cloud, filters.start, filters.end, tenant_key=filters.tenant_key)
    return filters


def ensure_ingest_v2_summary(
    filters: QueryFilters = Depends(parse_finops_filters),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> QueryFilters:
    reference_date = filters.end
    year_start = reference_date.replace(month=1, day=1)
    tenant = TenantService(db).resolve_tenant(filters.cloud, filters.tenant_key)
    filters.tenant_id = tenant.tenant_id if tenant else None
    if refresh:
        providers = ["aws", "azure", "oci"] if filters.cloud == "all" else [filters.cloud]
        for provider in providers:
            tenant_keys = _tenant_keys_for_request(db, provider, filters.tenant_key if provider == filters.cloud else None)
            for current_tenant_key in tenant_keys:
                run_ingest_job(db, provider=provider, start=year_start, end=reference_date, tenant_key=current_tenant_key)
        CurrencyRateSyncService(db).ensure_brl_usd_rate(date.today())
    else:
        AutoIngestService(db).ensure_range(filters.cloud, year_start, reference_date, tenant_key=filters.tenant_key)
        CurrencyRateSyncService(db).ensure_brl_usd_rate(date.today())
    # O summary usa acumulados mensal/anual e deve ser resiliente a cobertura parcial.
    # Quando faltarem dados no intervalo, seguimos com os dados disponiveis em vez de
    # interromper o dashboard com 409.
    try:
        _assert_data_available(db, filters.cloud, filters.start, filters.end, tenant_id=filters.tenant_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT:
            logger.warning(
                "Summary com cobertura parcial para cloud=%s tenant_id=%s intervalo=%s..%s: %s",
                filters.cloud,
                filters.tenant_id,
                filters.start,
                filters.end,
                exc.detail,
            )
        else:
            raise
    return filters


def parse_group_by(group_by: str = Query(default="service", alias="groupBy", pattern="^(service|account)$")) -> str:
    return group_by


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
    tenant_key: str | None = Query(default=None, alias="tenant_key"),
    month: str | None = Query(default=None),
    service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db),
) -> FiltersV2Response:
    try:
        tenant = TenantService(db).resolve_tenant(cloud, tenant_key)
        return FiltersV2Response(**service.filters_v2(cloud=cloud, month=month, tenant_id=tenant.tenant_id if tenant else None))
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


@router.post("/analytics/insights", response_model=AnalyticsInsightResponse)
def post_analytics_insights_v2(
    payload: AnalyticsInsightRequest,
    service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db),
) -> AnalyticsInsightResponse:
    tenant = TenantService(db).resolve_tenant(payload.cloud, payload.tenant_key)
    filters = QueryFilters(
        cloud=payload.cloud,
        tenant_id=tenant.tenant_id if tenant else None,
        tenant_key=payload.tenant_key,
        start=payload.from_,
        end=payload.to,
        currency=payload.currency,
        services=payload.services or None,
        accounts=payload.accounts or None,
    )
    return AnalyticsInsightService(service).generate(filters=filters, top_n=payload.topN)


@router.get("/cost-explorer/snapshot", response_model=CostExplorerSnapshotResponse)
def get_cost_explorer_snapshot_v2(
    filters: QueryFilters = Depends(ensure_ingest_v2_summary),
    top_n: int = Query(default=10, alias="topN", ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
) -> CostExplorerSnapshotResponse:
    return CostExplorerService(service).snapshot(filters=filters, top_n=top_n)


@router.get("/cost-explorer/breakdown", response_model=list[CostExplorerBreakdownItem])
def get_cost_explorer_breakdown_v2(
    filters: QueryFilters = Depends(ensure_ingest_v2_refreshable),
    group_by: str = Depends(parse_group_by),
    top_n: int = Query(default=10, alias="topN", ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[CostExplorerBreakdownItem]:
    return CostExplorerService(service).breakdown(filters=filters, top_n=top_n, group_by=group_by)


@router.get("/cost-explorer/trend", response_model=list[CostExplorerTrendItem])
def get_cost_explorer_trend_v2(
    filters: QueryFilters = Depends(ensure_ingest_v2_refreshable),
    group_by: str = Depends(parse_group_by),
    selected_item: str | None = Query(default=None, alias="selectedItem"),
    top_n: int = Query(default=10, alias="topN", ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[CostExplorerTrendItem]:
    return CostExplorerService(service).trend(
        filters=filters,
        group_by=group_by,
        selected_item=selected_item,
        top_n=top_n,
    )


@router.post("/cost-explorer/insights", response_model=CostExplorerInsightResponse)
def post_cost_explorer_insights_v2(
    payload: CostExplorerInsightRequest,
    service: AnalyticsService = Depends(get_analytics_service),
    db: Session = Depends(get_db),
) -> CostExplorerInsightResponse:
    tenant = TenantService(db).resolve_tenant(payload.cloud, payload.tenant_key)
    AutoIngestService(db).ensure_range(payload.cloud, payload.from_, payload.to, tenant_key=payload.tenant_key)
    filters = QueryFilters(
        cloud=payload.cloud,
        tenant_id=tenant.tenant_id if tenant else None,
        tenant_key=payload.tenant_key,
        start=payload.from_,
        end=payload.to,
        currency=payload.currency,
        services=payload.services or None,
        accounts=payload.accounts or None,
    )
    return CostExplorerInsightService(CostExplorerService(service)).generate(
        filters=filters,
        top_n=payload.topN,
        group_by=payload.groupBy,
        selected_item=payload.selectedItem,
    )


@router.post("/reingest", response_model=ReingestResponse)
def post_reingest(payload: ReingestRequest, db: Session = Depends(get_db)) -> ReingestResponse:
    if payload.from_ > payload.to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="from deve ser menor ou igual a to")
    range_days = (payload.to - payload.from_).days
    if range_days > settings.ingest_max_range_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Intervalo de {range_days} dias excede o maximo permitido de {settings.ingest_max_range_days} dias",
        )
    cloud = payload.cloud.lower().strip()
    if cloud not in {"aws", "azure", "oci", "all"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cloud inválida")

    providers = ["aws", "azure", "oci"] if cloud == "all" else [cloud]
    results: list[ReingestResult] = []
    try:
        for provider in providers:
            tenant_keys = _tenant_keys_for_request(db, provider, payload.tenant_key if provider == cloud else None)
            for current_tenant_key in tenant_keys:
                result = run_ingest_job(db, provider=provider, start=payload.from_, end=payload.to, tenant_key=current_tenant_key)
                results.append(ReingestResult(**result))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    CurrencyRateSyncService(db).ensure_brl_usd_rate(payload.to)
    return ReingestResponse(results=results)
