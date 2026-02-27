from __future__ import annotations

from datetime import date

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from finops_api.db.session import get_db
from finops_api.repositories.dims_repo import DimsRepository
from finops_api.repositories.currency_rate_repo import CurrencyRateRepository
from finops_api.repositories.fact_cost_repo import FactCostRepository, QueryFilters
from finops_api.services.analytics_service import AnalyticsService
from finops_api.services.auto_ingest_service import AutoIngestService
from finops_api.services.filters_service import FiltersService
from finops_api.services.targets_service import TargetsService


def get_fact_repo(db: Session = Depends(get_db)) -> FactCostRepository:
    return FactCostRepository(db)


def get_dims_repo(db: Session = Depends(get_db)) -> DimsRepository:
    return DimsRepository(db)


def get_currency_rate_repo(db: Session = Depends(get_db)) -> CurrencyRateRepository:
    return CurrencyRateRepository(db)


def get_targets_service() -> TargetsService:
    return TargetsService()


def get_analytics_service(
    repo: FactCostRepository = Depends(get_fact_repo),
    currency_repo: CurrencyRateRepository = Depends(get_currency_rate_repo),
    targets: TargetsService = Depends(get_targets_service),
) -> AnalyticsService:
    return AnalyticsService(repo, currency_repo=currency_repo, targets=targets)


def get_filters_service(
    dims_repo: DimsRepository = Depends(get_dims_repo),
    fact_repo: FactCostRepository = Depends(get_fact_repo),
) -> FiltersService:
    return FiltersService(dims_repo, fact_repo)


def parse_filters(
    cloud: str = Query(default="all", pattern="^(aws|azure|oci|all)$"),
    start: date = Query(...),
    end: date = Query(...),
    scope_key: str | None = Query(default=None),
    service_key: str | None = Query(default=None),
) -> QueryFilters:
    if start > end:
        raise ValueError("start deve ser menor ou igual a end")
    return QueryFilters(
        cloud=cloud,
        start=start,
        end=end,
        scope_key=scope_key,
        service_key=service_key,
    )


def ensure_auto_ingest_for_filters(
    filters: QueryFilters = Depends(parse_filters),
    db: Session = Depends(get_db),
) -> QueryFilters:
    AutoIngestService(db).ensure_range(filters.cloud, filters.start, filters.end)
    return filters
