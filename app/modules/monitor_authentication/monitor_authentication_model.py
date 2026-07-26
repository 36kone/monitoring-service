from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

from .login_body_type import LoginBodyType
from .monitor_authentication_enum import MonitorAuthenticationTypeEnum

if TYPE_CHECKING:
    from ..monitor.monitor_model import Monitor


class MonitorAuthentication(Base):
    __tablename__ = "monitor_authentications"
    __table_args__ = (UniqueConstraint("monitor_id", name="uq_monitor_authentications_monitor_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    monitor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False
    )
    auth_type: Mapped[MonitorAuthenticationTypeEnum] = mapped_column(
        String(32), nullable=False, default=MonitorAuthenticationTypeEnum.NONE
    )
    encrypted_credentials: Mapped[str | None] = mapped_column(String, nullable=True)
    nonce: Mapped[str | None] = mapped_column(String(64), nullable=True)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    login_url: Mapped[str | None] = mapped_column(String, nullable=True)
    login_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    login_body_type: Mapped[LoginBodyType] = mapped_column(String(32), nullable=False, default=LoginBodyType.JSON)
    token_json_path: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_in_json_path: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at_json_path: Mapped[str | None] = mapped_column(String, nullable=True)
    authorization_header: Mapped[str] = mapped_column(String(255), nullable=False, default="Authorization")
    authorization_scheme: Mapped[str] = mapped_column(String(64), nullable=False, default="Bearer")
    refresh_skew_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    monitor: Mapped["Monitor"] = relationship("Monitor", lazy="noload")
