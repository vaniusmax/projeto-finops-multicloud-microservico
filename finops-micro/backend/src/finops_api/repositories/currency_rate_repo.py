from __future__ import annotations

from datetime import date

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import Session

from finops_api.models.dim_currency_rate import DimCurrencyRate


class CurrencyRateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_brl_per_usd(self, as_of: date) -> float | None:
        pairs = {("USD", "BRL"), ("BRL", "USD")}
        stmt = (
            select(
                DimCurrencyRate.rate_date,
                DimCurrencyRate.from_currency,
                DimCurrencyRate.to_currency,
                DimCurrencyRate.rate,
            )
            .where(DimCurrencyRate.rate_date <= as_of)
            .where(
                or_(
                    and_(DimCurrencyRate.from_currency == "USD", DimCurrencyRate.to_currency == "BRL"),
                    and_(DimCurrencyRate.from_currency == "BRL", DimCurrencyRate.to_currency == "USD"),
                )
            )
            .order_by(desc(DimCurrencyRate.rate_date))
        )
        rows = self.db.execute(stmt).all()
        for row in rows:
            from_currency = str(row.from_currency or "").upper()
            to_currency = str(row.to_currency or "").upper()
            if (from_currency, to_currency) not in pairs:
                continue
            rate = float(row.rate or 0.0)
            if rate <= 0:
                continue
            if from_currency == "USD" and to_currency == "BRL":
                return rate
            if from_currency == "BRL" and to_currency == "USD":
                return (1.0 / rate) if rate > 0 else None
        return None

