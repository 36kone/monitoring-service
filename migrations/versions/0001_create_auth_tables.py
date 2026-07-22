"""create auth tables

Revision ID: 0001
Revises:
Create Date: 2026-07-20

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS auth"))

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("password_recovery", sa.String(), nullable=True),
        sa.Column("password_recovery_expire", sa.DateTime(), nullable=True),
        sa.Column("single_session", sa.Boolean(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=True),
        sa.Column("mfa_secret", sa.String(), nullable=True),
        sa.Column("online_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("allow_virtual_agent", sa.Boolean(), nullable=False),
        sa.Column("is_super_user", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["auth.users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        schema="auth",
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revoked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expire_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("ipv4", sa.String(), nullable=True),
        sa.Column("ipv6", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["revoked_by"], ["auth.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="auth",
    )


def downgrade() -> None:
    op.drop_table("user_sessions", schema="auth")
    op.drop_table("users", schema="auth")
    op.execute(sa.text("DROP SCHEMA IF EXISTS auth"))
