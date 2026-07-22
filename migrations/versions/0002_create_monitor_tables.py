"""create monitor tables

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "unknown",
        "up",
        "down",
        "degraded",
        name="monitor_status_enum",
    )
    status_enum.create(op.get_bind(), checkfirst=True)
    status_column_enum = postgresql.ENUM(
        "unknown",
        "up",
        "down",
        "degraded",
        name="monitor_status_enum",
        create_type=False,
    )
    op.create_table(
        "monitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("timeout_ms", sa.Integer(), nullable=False, server_default="5000"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", status_column_enum, nullable=False, server_default="unknown"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_successes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_checked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("next_check_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.CheckConstraint("interval_seconds > 0", name="ck_monitors_interval_positive"),
        sa.CheckConstraint("timeout_ms > 0", name="ck_monitors_timeout_positive"),
        sa.CheckConstraint("consecutive_failures >= 0", name="ck_monitors_failures_nonnegative"),
        sa.CheckConstraint("consecutive_successes >= 0", name="ck_monitors_successes_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("monitors")
    sa.Enum(name="monitor_status_enum").drop(op.get_bind(), checkfirst=True)
