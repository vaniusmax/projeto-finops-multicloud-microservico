from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finops_api.db.base import Base


class FactIngestAudit(Base):
    __tablename__ = "fact_ingest_audit"

    audit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingest_job.job_id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dim_tenant.tenant_id"), nullable=False, index=True)
    cloud: Mapped[str] = mapped_column(String(16), nullable=False)
    fact_table: Mapped[str] = mapped_column(String(128), nullable=False, server_default=text("'fact_cost_daily'"))
    rows_inserted: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    rows_updated: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    rows_deleted: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job = relationship("IngestJob", back_populates="audits")
