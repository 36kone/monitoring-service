from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, Field, field_validator

from app.schemas.base import BaseSchema

from .monitor_enum import MonitorStatusEnum


class CreateMonitor(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    url: AnyHttpUrl
    method: str = Field(min_length=1, max_length=20)
    interval_seconds: int = Field(default=60, gt=0)
    timeout_ms: int = Field(default=5000, gt=0)
    enabled: bool = True

    @field_validator("method", mode="before")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.strip().upper()


class UpdateMonitor(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: AnyHttpUrl | None = None
    method: str | None = Field(default=None, min_length=1, max_length=20)
    interval_seconds: int | None = Field(default=None, gt=0)
    timeout_ms: int | None = Field(default=None, gt=0)
    enabled: bool | None = None

    @field_validator("method", mode="before")
    @classmethod
    def normalize_method(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None


class MonitorResponse(BaseSchema):
    id: UUID
    name: str
    url: str
    method: str
    interval_seconds: int
    timeout_ms: int
    enabled: bool
    status: MonitorStatusEnum
    consecutive_failures: int
    consecutive_successes: int
    last_checked_at: datetime | None
    next_check_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MonitorSearchRequest(BaseSchema):
    keyword: str | None = None
    enabled: bool | None = None
    status: MonitorStatusEnum | None = None
    size: int = Field(default=10, ge=1, le=100)
    page: int = Field(default=1, ge=1)
