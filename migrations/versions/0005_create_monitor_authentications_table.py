"""create monitor authentications table

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "monitor_authentications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("monitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("auth_type", sa.String(length=32), nullable=False, server_default="none"),
        sa.Column("encrypted_credentials", sa.String(), nullable=True),
        sa.Column("nonce", sa.String(length=64), nullable=True),
        sa.Column("key_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("login_url", sa.String(), nullable=True),
        sa.Column("login_method", sa.String(length=10), nullable=True),
        sa.Column("token_json_path", sa.String(), nullable=True),
        sa.Column("expires_in_json_path", sa.String(), nullable=True),
        sa.Column("expires_at_json_path", sa.String(), nullable=True),
        sa.Column("authorization_header", sa.String(length=255), nullable=False, server_default="Authorization"),
        sa.Column("authorization_scheme", sa.String(length=64), nullable=False, server_default="Bearer"),
        sa.Column("refresh_skew_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("monitor_id", name="uq_monitor_authentications_monitor_id"),
    )


def downgrade() -> None:
    op.drop_table("monitor_authentications")
