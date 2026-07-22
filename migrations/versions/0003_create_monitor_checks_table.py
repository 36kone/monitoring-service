"""create monitor checks table

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "unknown",
        "up",
        "down",
        "degraded",
        name="monitor_status_enum",
        create_type=False,
    )

    op.create_table(
        "monitor_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("monitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="unknown"),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("timed_out", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "checked_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status_code IS NULL OR (status_code >= 100 AND status_code <= 599)",
            name="ck_monitor_checks_status_code_range",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_monitor_checks_latency_nonnegative",
        ),
        sa.ForeignKeyConstraint(["monitor_id"], ["monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("monitor_checks")
