from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .user_session_model import UserSession


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}  # noqa: RUF012

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    password_recovery: Mapped[str | None] = mapped_column(String, nullable=True)
    password_recovery_expire: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    single_session: Mapped[bool | None] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mfa_enabled: Mapped[bool | None] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    online_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    allow_virtual_agent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_super_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        foreign_keys="UserSession.user_id",
        back_populates="user",
        lazy="noload",
    )

    revoked_sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        foreign_keys="UserSession.revoked_by",
        back_populates="who_revoked",
        lazy="noload",
    )

    who_created: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by],
        remote_side=[id],
        post_update=True,
        lazy="noload",
    )

    who_updated: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[updated_by],
        remote_side=[id],
        post_update=True,
        lazy="noload",
    )
