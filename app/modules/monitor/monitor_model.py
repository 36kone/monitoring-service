from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import JSON, TIMESTAMP, Boolean, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

from .monitor_enum import MonitorStatusEnum

if TYPE_CHECKING:
    from ..incident.incident_model import Incident
    from ..monitor_check.monitor_check_model import MonitorCheck


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=5000)
    request_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    request_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[MonitorStatusEnum] = mapped_column(
        Enum(
            MonitorStatusEnum,
            name="monitor_status_enum",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=MonitorStatusEnum.UNKNOWN,
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_checked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    next_check_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    checks: Mapped[list["MonitorCheck"]] = relationship(
        "MonitorCheck",
        back_populates="monitor",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="monitor",
        cascade="all, delete-orphan",
        lazy="noload",
    )
