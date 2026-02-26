from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finops_api.db.base import Base


class FactCostDaily(Base):
    __tablename__ = "fact_cost_daily"
    __table_args__ = (Index("ix_fact_cost_daily_usage_date_cloud", "cost_date", "cloud"),)

    fact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usage_date: Mapped[date] = mapped_column("cost_date", Date, nullable=False, index=True)
    cloud: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("dim_scope.scope_id"), nullable=True)
    service_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("dim_service.service_id"), nullable=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("dim_region.region_id"), nullable=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("ingest_job.job_id"), nullable=True)

    scope_key: Mapped[str] = mapped_column(String(256), nullable=False)
    service_key: Mapped[str] = mapped_column(String(256), nullable=False)
    region_key: Mapped[str | None] = mapped_column(String(256), nullable=True)

    currency_code: Mapped[str] = mapped_column("currency", String(8), nullable=False, default="USD")
    amount: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    amount_brl: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    fx_rate_used: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    charge_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pricing_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meter_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    meter_subcategory: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    source_ref: Mapped[str] = mapped_column("source", String(128), nullable=False, default="unknown")
    source_record_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("raw", JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    scope = relationship("DimScope", back_populates="costs")
    service = relationship("DimService", back_populates="costs")
    region = relationship("DimRegion", back_populates="costs")
