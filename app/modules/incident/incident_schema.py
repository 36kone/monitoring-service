from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema

from .incident_enum import IncidentStatusEnum


class CreateIncident(BaseSchema):
    status: IncidentStatusEnum = IncidentStatusEnum.OPEN
    started_at: datetime | None = None
    resolved_at: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.resolved_at is not None
            and self.started_at is not None
            and self.resolved_at < self.started_at
        ):
            raise ValueError("resolved_at must be after started_at")
        if self.status is IncidentStatusEnum.OPEN and self.resolved_at is not None:
            raise ValueError("Open incidents cannot have resolved_at")
        if self.status is IncidentStatusEnum.RESOLVED and self.resolved_at is None:
            raise ValueError("Resolved incidents require resolved_at")
        return self


class UpdateIncident(BaseSchema):
    status: IncidentStatusEnum | None = None
    started_at: datetime | None = None
    resolved_at: datetime | None = None
    duration_seconds: int | None = Field(default=None, ge=0)


class IncidentResponse(BaseSchema):
    id: UUID
    monitor_id: UUID
    status: IncidentStatusEnum
    started_at: datetime
    resolved_at: datetime | None
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime


class IncidentSearchRequest(BaseSchema):
    status: IncidentStatusEnum | None = None
    size: int = Field(default=10, ge=1, le=100)
    page: int = Field(default=1, ge=1)
