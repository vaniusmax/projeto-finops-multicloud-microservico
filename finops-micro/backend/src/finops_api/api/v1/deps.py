from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from finops_api.db.session import get_db
from finops_api.repositories.currency_rate_repo import CurrencyRateRepository
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.services.analytics_service import AnalyticsService
from finops_api.services.targets_service import TargetsService


def get_fact_repo(db: Session = Depends(get_db)) -> FactCostRepository:
    return FactCostRepository(db)


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
