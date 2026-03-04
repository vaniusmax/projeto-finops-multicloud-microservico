"""auth tables

Revision ID: 0003_auth
Revises: 0002_multi_tenant
Create Date: 2026-03-03 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0003_auth"
down_revision = "0002_multi_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("auth_user"):
        op.create_table(
            "auth_user",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("first_name", sa.String(length=128), nullable=False),
            sa.Column("last_name", sa.String(length=128), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("password_hash", sa.String(length=512), nullable=True),
            sa.Column("is_email_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("user_id", name=op.f("pk_auth_user")),
            sa.UniqueConstraint("email", name=op.f("uq_auth_user_email")),
        )
        op.create_index(op.f("ix_auth_user_email"), "auth_user", ["email"], unique=False)

    if not inspector.has_table("auth_email_verification_token"):
        op.create_table(
            "auth_email_verification_token",
            sa.Column("token_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["auth_user.user_id"], name=op.f("fk_auth_email_verification_token_user_id_auth_user"), ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("token_id", name=op.f("pk_auth_email_verification_token")),
            sa.UniqueConstraint("token_hash", name=op.f("uq_auth_email_verification_token_token_hash")),
        )
        op.create_index(op.f("ix_auth_email_verification_token_user_id"), "auth_email_verification_token", ["user_id"], unique=False)

    if not inspector.has_table("auth_session"):
        op.create_table(
            "auth_session",
            sa.Column("session_id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["auth_user.user_id"], name=op.f("fk_auth_session_user_id_auth_user"), ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("session_id", name=op.f("pk_auth_session")),
            sa.UniqueConstraint("token_hash", name=op.f("uq_auth_session_token_hash")),
        )
        op.create_index(op.f("ix_auth_session_user_id"), "auth_session", ["user_id"], unique=False)


def downgrade() -> None:
    if inspect(op.get_bind()).has_table("auth_session"):
        op.drop_index(op.f("ix_auth_session_user_id"), table_name="auth_session")
        op.drop_table("auth_session")
    if inspect(op.get_bind()).has_table("auth_email_verification_token"):
        op.drop_index(op.f("ix_auth_email_verification_token_user_id"), table_name="auth_email_verification_token")
        op.drop_table("auth_email_verification_token")
    if inspect(op.get_bind()).has_table("auth_user"):
        op.drop_index(op.f("ix_auth_user_email"), table_name="auth_user")
        op.drop_table("auth_user")
