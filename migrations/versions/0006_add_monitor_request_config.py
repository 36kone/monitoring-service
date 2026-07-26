"""add monitor request configuration

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("monitors", sa.Column("request_body", sa.JSON(), nullable=True))
    op.add_column("monitors", sa.Column("request_headers", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("monitors", "request_headers")
    op.drop_column("monitors", "request_body")
