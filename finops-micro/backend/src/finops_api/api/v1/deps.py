from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from finops_api.db.session import get_db
from finops_api.models.auth_user import AuthUser
from finops_api.repositories.currency_rate_repo import CurrencyRateRepository
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.services.auth_service import AuthService
from finops_api.services.analytics_service import AnalyticsService
from finops_api.services.targets_service import TargetsService


def get_fact_repo(db: Session = Depends(get_db)) -> FactCostRepository:
    return FactCostRepository(db)


def get_currency_rate_repo(db: Session = Depends(get_db)) -> CurrencyRateRepository:
    return CurrencyRateRepository(db)


def get_targets_service() -> TargetsService:
    return TargetsService()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_current_user(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthUser:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cabeçalho Authorization é obrigatório")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization deve usar Bearer token")
    try:
        return auth_service.get_user_by_access_token(token.strip())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def get_analytics_service(
    repo: FactCostRepository = Depends(get_fact_repo),
    currency_repo: CurrencyRateRepository = Depends(get_currency_rate_repo),
    targets: TargetsService = Depends(get_targets_service),
) -> AnalyticsService:
    return AnalyticsService(repo, currency_repo=currency_repo, targets=targets)
