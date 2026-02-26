from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from finops_api.db.base import Base


class DimCurrencyRate(Base):
    __tablename__ = "dim_currency_rate"
    __table_args__ = (UniqueConstraint("rate_date", "from_currency", "to_currency"),)

    rate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    from_currency: Mapped[str] = mapped_column(String(8), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(8), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
