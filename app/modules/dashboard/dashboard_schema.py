from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema


class DashboardUptimePoint(BaseSchema):
    date: str
    uptime: float


class DashboardMonitor(BaseSchema):
    id: UUID
    name: str
    url: str
    method: str
    status: str
    enabled: bool
    interval_seconds: int
    last_checked_at: datetime | None
    last_latency_ms: int | None


class DashboardIncident(BaseSchema):
    id: UUID
    monitor_id: UUID
    monitor_name: str
    status: str
    started_at: datetime
    resolved_at: datetime | None
    duration_seconds: int | None


class DashboardHomeResponse(BaseSchema):
    overall_uptime: float
    average_latency_ms: float
    active_monitors: int
    operational_monitors: int
    open_incidents: int
    uptime_series: list[DashboardUptimePoint]
    recent_incidents: list[DashboardIncident]
    monitors: list[DashboardMonitor]
