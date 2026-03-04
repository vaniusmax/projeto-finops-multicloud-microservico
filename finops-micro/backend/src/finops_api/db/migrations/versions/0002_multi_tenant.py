"""multi tenant support

Revision ID: 0002_multi_tenant
Revises: 0001_canonical_v0
Create Date: 2026-03-03 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_multi_tenant"
down_revision = "0001_canonical_v0"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_unique_constraint(inspector, table_name: str, constraint_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(
        constraint["name"] == constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    if not _has_table(inspector, "dim_tenant"):
        op.create_table(
            "dim_tenant",
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("cloud", sa.String(length=16), nullable=False),
            sa.Column("tenant_key", sa.String(length=128), nullable=False),
            sa.Column("tenant_name", sa.String(length=256), nullable=True),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.PrimaryKeyConstraint("tenant_id", name=op.f("pk_dim_tenant")),
            sa.UniqueConstraint("cloud", "tenant_key", name=op.f("uq_dim_tenant_cloud_tenant_key")),
        )
        op.create_index(op.f("ix_dim_tenant_cloud"), "dim_tenant", ["cloud"], unique=False)

    if _has_table(inspector, "dim_scope") and not _has_column(inspector, "dim_scope", "tenant_id"):
        op.add_column("dim_scope", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(op.f("fk_dim_scope_tenant_id_dim_tenant"), "dim_scope", "dim_tenant", ["tenant_id"], ["tenant_id"])
        op.create_index(op.f("ix_dim_scope_tenant_id"), "dim_scope", ["tenant_id"], unique=False)

    if _has_table(inspector, "fact_cost_daily") and not _has_column(inspector, "fact_cost_daily", "tenant_id"):
        op.add_column("fact_cost_daily", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            op.f("fk_fact_cost_daily_tenant_id_dim_tenant"),
            "fact_cost_daily",
            "dim_tenant",
            ["tenant_id"],
            ["tenant_id"],
        )
        op.create_index(op.f("ix_fact_cost_daily_tenant_id"), "fact_cost_daily", ["tenant_id"], unique=False)

    if _has_table(inspector, "ingest_job") and not _has_column(inspector, "ingest_job", "tenant_id"):
        op.add_column("ingest_job", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(op.f("fk_ingest_job_tenant_id_dim_tenant"), "ingest_job", "dim_tenant", ["tenant_id"], ["tenant_id"])
        op.create_index(op.f("ix_ingest_job_tenant_id"), "ingest_job", ["tenant_id"], unique=False)

    if not _has_table(inspector, "fact_ingest_audit"):
        op.create_table(
            "fact_ingest_audit",
            sa.Column("audit_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("cloud", sa.String(length=16), nullable=False),
            sa.Column("fact_table", sa.String(length=128), nullable=False, server_default=sa.text("'fact_cost_daily'")),
            sa.Column("rows_inserted", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("rows_updated", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("rows_deleted", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["job_id"], ["ingest_job.job_id"], name=op.f("fk_fact_ingest_audit_job_id_ingest_job"), ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("audit_id", name=op.f("pk_fact_ingest_audit")),
        )

    if _has_table(inspector, "fact_ingest_audit") and not _has_column(inspector, "fact_ingest_audit", "tenant_id"):
        op.add_column("fact_ingest_audit", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            op.f("fk_fact_ingest_audit_tenant_id_dim_tenant"),
            "fact_ingest_audit",
            "dim_tenant",
            ["tenant_id"],
            ["tenant_id"],
        )
        op.create_index(op.f("ix_fact_ingest_audit_tenant_id"), "fact_ingest_audit", ["tenant_id"], unique=False)

    op.execute(
        """
        INSERT INTO dim_tenant (cloud, tenant_key, tenant_name, metadata)
        SELECT cloud, scope_key, NULLIF(scope_name, ''), jsonb_build_object('backfill', true, 'source', 'scope_root')
        FROM dim_scope
        WHERE scope_type IN ('oci_tenancy', 'azure_subscription', 'aws_account')
        ON CONFLICT (cloud, tenant_key) DO UPDATE
        SET tenant_name = COALESCE(EXCLUDED.tenant_name, dim_tenant.tenant_name),
            updated_at = now();
        """
    )
    op.execute(
        """
        INSERT INTO dim_tenant (cloud, tenant_key, tenant_name, metadata)
        SELECT DISTINCT cloud, 'default', initcap(cloud::text) || ' Default', jsonb_build_object('backfill', true, 'source', 'default')
        FROM (
            SELECT cloud FROM dim_scope
            UNION
            SELECT cloud FROM fact_cost_daily
            UNION
            SELECT cloud FROM ingest_job
        ) clouds
        ON CONFLICT (cloud, tenant_key) DO NOTHING;
        """
    )

    op.execute(
        """
        UPDATE dim_scope AS ds
        SET tenant_id = dt.tenant_id
        FROM dim_tenant AS dt
        WHERE ds.tenant_id IS NULL
          AND ds.cloud = dt.cloud
          AND ds.scope_key = dt.tenant_key;
        """
    )
    op.execute(
        """
        UPDATE dim_scope AS ds
        SET tenant_id = dt.tenant_id
        FROM dim_scope AS parent_scope
        JOIN dim_tenant AS dt
          ON dt.cloud = parent_scope.cloud
         AND dt.tenant_key = parent_scope.scope_key
        WHERE ds.tenant_id IS NULL
          AND ds.parent_scope_key IS NOT NULL
          AND parent_scope.cloud = ds.cloud
          AND parent_scope.scope_key = ds.parent_scope_key
          AND parent_scope.scope_type IN ('oci_tenancy', 'azure_subscription', 'aws_account');
        """
    )
    op.execute(
        """
        UPDATE dim_scope AS ds
        SET tenant_id = dt.tenant_id
        FROM dim_tenant AS dt
        WHERE ds.tenant_id IS NULL
          AND ds.cloud = dt.cloud
          AND dt.tenant_key = 'default';
        """
    )

    op.execute(
        """
        INSERT INTO dim_scope (tenant_id, cloud, scope_type, scope_key, scope_name, metadata)
        SELECT dt.tenant_id, f.cloud, 'unknown', f.scope_key, f.scope_key, jsonb_build_object('backfill', true, 'source', 'fact_cost_daily')
        FROM (
            SELECT DISTINCT cloud, scope_key
            FROM fact_cost_daily
            WHERE scope_key IS NOT NULL
        ) AS f
        JOIN dim_tenant AS dt
          ON dt.cloud = f.cloud
         AND dt.tenant_key = 'default'
        LEFT JOIN dim_scope AS ds
          ON ds.cloud = f.cloud
         AND ds.scope_key = f.scope_key
         AND ds.tenant_id = dt.tenant_id
        WHERE ds.scope_id IS NULL
        ON CONFLICT (tenant_id, scope_key) DO NOTHING;
        """
    )

    op.execute(
        """
        UPDATE fact_cost_daily AS f
        SET scope_id = ds.scope_id
        FROM dim_scope AS ds
        WHERE f.scope_id IS NULL
          AND ds.cloud = f.cloud
          AND ds.scope_key = f.scope_key;
        """
    )
    op.execute(
        """
        UPDATE fact_cost_daily AS f
        SET tenant_id = ds.tenant_id
        FROM dim_scope AS ds
        WHERE f.tenant_id IS NULL
          AND ds.scope_id = f.scope_id;
        """
    )
    op.execute(
        """
        UPDATE fact_cost_daily AS f
        SET tenant_id = dt.tenant_id
        FROM dim_tenant AS dt
        WHERE f.tenant_id IS NULL
          AND dt.cloud = f.cloud
          AND dt.tenant_key = 'default';
        """
    )

    op.execute(
        """
        UPDATE ingest_job AS job
        SET tenant_id = dt.tenant_id
        FROM dim_tenant AS dt
        WHERE job.tenant_id IS NULL
          AND dt.cloud = job.cloud
          AND dt.tenant_key = 'default';
        """
    )

    op.execute(
        """
        UPDATE fact_ingest_audit AS audit
        SET tenant_id = job.tenant_id
        FROM ingest_job AS job
        WHERE audit.tenant_id IS NULL
          AND audit.job_id = job.job_id;
        """
    )
    op.execute(
        """
        UPDATE fact_ingest_audit AS audit
        SET tenant_id = dt.tenant_id
        FROM dim_tenant AS dt
        WHERE audit.tenant_id IS NULL
          AND dt.cloud = audit.cloud
          AND dt.tenant_key = 'default';
        """
    )

    op.alter_column("dim_scope", "tenant_id", nullable=False)
    op.alter_column("fact_cost_daily", "tenant_id", nullable=False)
    op.alter_column("fact_cost_daily", "scope_id", nullable=False)
    op.alter_column("ingest_job", "tenant_id", nullable=False)
    op.alter_column("fact_ingest_audit", "tenant_id", nullable=False)

    if _has_unique_constraint(inspector, "dim_scope", "uq_dim_scope_cloud"):
        op.drop_constraint("uq_dim_scope_cloud", "dim_scope", type_="unique")
    op.create_unique_constraint(op.f("uq_dim_scope_tenant_id"), "dim_scope", ["tenant_id", "scope_key"])

    if not _has_index(inspector, "fact_cost_daily", "ix_fact_cost_daily_tenant_cost_date"):
        op.create_index("ix_fact_cost_daily_tenant_cost_date", "fact_cost_daily", ["tenant_id", "cost_date"], unique=False)
    if not _has_index(inspector, "fact_cost_daily", "ix_fact_cost_daily_tenant_cloud_cost_date"):
        op.create_index(
            "ix_fact_cost_daily_tenant_cloud_cost_date",
            "fact_cost_daily",
            ["tenant_id", "cloud", "cost_date"],
            unique=False,
        )
    if not _has_index(inspector, "fact_cost_daily", "ix_fact_cost_daily_tenant_scope_cost_date"):
        op.create_index(
            "ix_fact_cost_daily_tenant_scope_cost_date",
            "fact_cost_daily",
            ["tenant_id", "scope_id", "cost_date"],
            unique=False,
        )
    if not _has_index(inspector, "fact_cost_daily", "ix_fact_cost_daily_tenant_service_cost_date"):
        op.create_index(
            "ix_fact_cost_daily_tenant_service_cost_date",
            "fact_cost_daily",
            ["tenant_id", "service_id", "cost_date"],
            unique=False,
        )
    if not _has_index(inspector, "fact_cost_daily", "ix_fact_cost_daily_tags_gin"):
        op.create_index("ix_fact_cost_daily_tags_gin", "fact_cost_daily", ["tags"], unique=False, postgresql_using="gin")
    if not _has_index(inspector, "fact_cost_daily", "ix_fact_cost_daily_raw_gin"):
        op.create_index("ix_fact_cost_daily_raw_gin", "fact_cost_daily", ["raw"], unique=False, postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_fact_cost_daily_raw_gin", table_name="fact_cost_daily")
    op.drop_index("ix_fact_cost_daily_tags_gin", table_name="fact_cost_daily")
    op.drop_index("ix_fact_cost_daily_tenant_service_cost_date", table_name="fact_cost_daily")
    op.drop_index("ix_fact_cost_daily_tenant_scope_cost_date", table_name="fact_cost_daily")
    op.drop_index("ix_fact_cost_daily_tenant_cloud_cost_date", table_name="fact_cost_daily")
    op.drop_index("ix_fact_cost_daily_tenant_cost_date", table_name="fact_cost_daily")

    op.drop_constraint(op.f("uq_dim_scope_tenant_id"), "dim_scope", type_="unique")
    op.create_unique_constraint("uq_dim_scope_cloud", "dim_scope", ["cloud", "scope_key"])

    op.drop_index(op.f("ix_fact_ingest_audit_tenant_id"), table_name="fact_ingest_audit")
    op.drop_constraint(op.f("fk_fact_ingest_audit_tenant_id_dim_tenant"), "fact_ingest_audit", type_="foreignkey")
    op.drop_column("fact_ingest_audit", "tenant_id")

    op.drop_index(op.f("ix_ingest_job_tenant_id"), table_name="ingest_job")
    op.drop_constraint(op.f("fk_ingest_job_tenant_id_dim_tenant"), "ingest_job", type_="foreignkey")
    op.drop_column("ingest_job", "tenant_id")

    op.drop_index(op.f("ix_fact_cost_daily_tenant_id"), table_name="fact_cost_daily")
    op.drop_constraint(op.f("fk_fact_cost_daily_tenant_id_dim_tenant"), "fact_cost_daily", type_="foreignkey")
    op.drop_column("fact_cost_daily", "tenant_id")

    op.drop_index(op.f("ix_dim_scope_tenant_id"), table_name="dim_scope")
    op.drop_constraint(op.f("fk_dim_scope_tenant_id_dim_tenant"), "dim_scope", type_="foreignkey")
    op.drop_column("dim_scope", "tenant_id")

    op.drop_index(op.f("ix_dim_tenant_cloud"), table_name="dim_tenant")
    op.drop_table("dim_tenant")
