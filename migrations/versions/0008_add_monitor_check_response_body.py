"""add response body to monitor checks

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("monitor_checks", sa.Column("response_body", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("monitor_checks", "response_body")
