from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema

from ..monitor.monitor_enum import MonitorStatusEnum


class CreateMonitorCheck(BaseSchema):
    status: MonitorStatusEnum = MonitorStatusEnum.UNKNOWN
    status_code: int | None = Field(default=None, ge=100, le=599)
    success: bool = False
    latency_ms: int | None = Field(default=None, ge=0)
    error: str | None = Field(default=None, max_length=1000)
    response_body: Any | None = None
    timed_out: bool = False


class UpdateMonitorCheck(BaseSchema):
    status: MonitorStatusEnum | None = None
    status_code: int | None = Field(default=None, ge=100, le=599)
    success: bool | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    error: str | None = Field(default=None, max_length=1000)
    response_body: Any | None = None
    timed_out: bool | None = None
    checked_at: datetime | None = None


class MonitorCheckResponse(BaseSchema):
    id: UUID
    monitor_id: UUID
    status: MonitorStatusEnum
    status_code: int | None
    success: bool
    latency_ms: int | None
    error: str | None
    response_body: Any | None
    timed_out: bool
    checked_at: datetime
    created_at: datetime
    updated_at: datetime


class MonitorCheckSearchRequest(BaseSchema):
    status: MonitorStatusEnum | None = None
    success: bool | None = None
    size: int = Field(default=10, ge=1, le=100)
    page: int = Field(default=1, ge=1)
