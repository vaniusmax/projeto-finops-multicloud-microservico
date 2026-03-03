from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finops_api.db.base import Base


class DimTenant(Base):
    __tablename__ = "dim_tenant"
    __table_args__ = (UniqueConstraint("cloud", "tenant_key"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cloud: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    tenant_key: Mapped[str] = mapped_column(String(128), nullable=False)
    tenant_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    scopes = relationship("DimScope", back_populates="tenant")
    costs = relationship("FactCostDaily", back_populates="tenant")
    jobs = relationship("IngestJob", back_populates="tenant")
