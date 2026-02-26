"""canonical v0

Revision ID: 0001_canonical_v0
Revises:
Create Date: 2026-02-26 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "0001_canonical_v0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("dim_scope"):
        # Schema ja inicializado por SQL bootstrap (docker-entrypoint-initdb.d).
        # Nessa situacao, apenas marcamos esta revisao como aplicada.
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        "dim_scope",
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cloud", sa.String(length=16), nullable=False),
        sa.Column("scope_key", sa.String(length=128), nullable=False),
        sa.Column("scope_name", sa.String(length=256), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("scope_id", name=op.f("pk_dim_scope")),
        sa.UniqueConstraint("cloud", "scope_key", name=op.f("uq_dim_scope_cloud")),
    )
    op.create_index(op.f("ix_dim_scope_cloud"), "dim_scope", ["cloud"], unique=False)

    op.create_table(
        "dim_service",
        sa.Column("service_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cloud", sa.String(length=16), nullable=False),
        sa.Column("service_key", sa.String(length=128), nullable=False),
        sa.Column("service_name", sa.String(length=256), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("service_id", name=op.f("pk_dim_service")),
        sa.UniqueConstraint("cloud", "service_key", name=op.f("uq_dim_service_cloud")),
    )
    op.create_index(op.f("ix_dim_service_cloud"), "dim_service", ["cloud"], unique=False)

    op.create_table(
        "dim_region",
        sa.Column("region_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cloud", sa.String(length=16), nullable=False),
        sa.Column("region_key", sa.String(length=128), nullable=False),
        sa.Column("region_name", sa.String(length=256), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("region_id", name=op.f("pk_dim_region")),
        sa.UniqueConstraint("cloud", "region_key", name=op.f("uq_dim_region_cloud")),
    )
    op.create_index(op.f("ix_dim_region_cloud"), "dim_region", ["cloud"], unique=False)

    op.create_table(
        "dim_currency_rate",
        sa.Column("rate_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("from_currency", sa.String(length=8), nullable=False),
        sa.Column("to_currency", sa.String(length=8), nullable=False),
        sa.Column("rate", sa.Numeric(precision=18, scale=8), nullable=False),
        sa.PrimaryKeyConstraint("rate_id", name=op.f("pk_dim_currency_rate")),
        sa.UniqueConstraint("rate_date", "from_currency", "to_currency", name=op.f("uq_dim_currency_rate_rate_date")),
    )
    op.create_index(op.f("ix_dim_currency_rate_rate_date"), "dim_currency_rate", ["rate_date"], unique=False)

    op.create_table(
        "ingest_job",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("provider", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("job_id", name=op.f("pk_ingest_job")),
    )
    op.create_index(op.f("ix_ingest_job_provider"), "ingest_job", ["provider"], unique=False)
    op.create_index(op.f("ix_ingest_job_status"), "ingest_job", ["status"], unique=False)

    op.create_table(
        "fact_cost_daily",
        sa.Column("fact_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("cloud", sa.String(length=16), nullable=False),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("currency_code", sa.String(length=8), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("amount_brl", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("source_ref", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["dim_region.region_id"], name=op.f("fk_fact_cost_daily_region_id_dim_region")),
        sa.ForeignKeyConstraint(["scope_id"], ["dim_scope.scope_id"], name=op.f("fk_fact_cost_daily_scope_id_dim_scope")),
        sa.ForeignKeyConstraint(["service_id"], ["dim_service.service_id"], name=op.f("fk_fact_cost_daily_service_id_dim_service")),
        sa.PrimaryKeyConstraint("fact_id", name=op.f("pk_fact_cost_daily")),
        sa.UniqueConstraint(
            "usage_date",
            "cloud",
            "scope_id",
            "service_id",
            "region_id",
            "currency_code",
            "source_ref",
            name=op.f("uq_fact_cost_daily_usage_date"),
        ),
    )
    op.create_index(op.f("ix_fact_cost_daily_cloud"), "fact_cost_daily", ["cloud"], unique=False)
    op.create_index(op.f("ix_fact_cost_daily_usage_date"), "fact_cost_daily", ["usage_date"], unique=False)
    op.create_index("ix_fact_cost_daily_usage_date_cloud", "fact_cost_daily", ["usage_date", "cloud"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_fact_cost_daily_usage_date_cloud", table_name="fact_cost_daily")
    op.drop_index(op.f("ix_fact_cost_daily_usage_date"), table_name="fact_cost_daily")
    op.drop_index(op.f("ix_fact_cost_daily_cloud"), table_name="fact_cost_daily")
    op.drop_table("fact_cost_daily")

    op.drop_index(op.f("ix_ingest_job_status"), table_name="ingest_job")
    op.drop_index(op.f("ix_ingest_job_provider"), table_name="ingest_job")
    op.drop_table("ingest_job")

    op.drop_index(op.f("ix_dim_currency_rate_rate_date"), table_name="dim_currency_rate")
    op.drop_table("dim_currency_rate")

    op.drop_index(op.f("ix_dim_region_cloud"), table_name="dim_region")
    op.drop_table("dim_region")

    op.drop_index(op.f("ix_dim_service_cloud"), table_name="dim_service")
    op.drop_table("dim_service")

    op.drop_index(op.f("ix_dim_scope_cloud"), table_name="dim_scope")
    op.drop_table("dim_scope")
