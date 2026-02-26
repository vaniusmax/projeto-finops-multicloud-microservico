from __future__ import annotations

import uuid

from sqlalchemy import String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finops_api.db.base import Base


class DimService(Base):
    __tablename__ = "dim_service"
    __table_args__ = (UniqueConstraint("cloud", "service_key"),)

    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cloud: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    service_name: Mapped[str] = mapped_column(String(256), nullable=False)
    raw_service: Mapped[str | None] = mapped_column(String(256), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    costs = relationship("FactCostDaily", back_populates="service")
