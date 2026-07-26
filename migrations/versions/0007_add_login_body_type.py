"""add login body type

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("monitor_authentications", sa.Column("login_body_type", sa.String(length=32), nullable=True))
    op.execute("UPDATE monitor_authentications SET login_body_type = 'json' WHERE login_body_type IS NULL")
    op.alter_column("monitor_authentications", "login_body_type", nullable=False, server_default="json")


def downgrade() -> None:
    op.drop_column("monitor_authentications", "login_body_type")
