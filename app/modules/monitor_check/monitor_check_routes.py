from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db.database import get_db
from app.dependencies.authentication import auth_guard
from app.dependencies.rate_limit import rate_limited
from app.schemas import PaginatedResponse

from .monitor_check_schema import (
    CreateMonitorCheck,
    MonitorCheckResponse,
    MonitorCheckSearchRequest,
    UpdateMonitorCheck,
)
from .monitor_check_service import MonitorCheckService

monitor_check_router = APIRouter(
    dependencies=[Depends(auth_guard)],
    route_class=rate_limited("100/minute"),
)


@monitor_check_router.post(
    "/{monitor_id}/checks/", status_code=201, response_model=MonitorCheckResponse
)
async def create_monitor_check(monitor_id: UUID, data: CreateMonitorCheck):
    async with get_db() as db:
        return await MonitorCheckService(db).create(monitor_id, data)


@monitor_check_router.get(
    "/{monitor_id}/checks/", response_model=PaginatedResponse[MonitorCheckResponse]
)
async def search_monitor_checks(
    monitor_id: UUID,
    filters: Annotated[MonitorCheckSearchRequest, Query()],
):
    async with get_db() as db:
        return await MonitorCheckService(db).search(monitor_id, filters)


@monitor_check_router.get("/{monitor_id}/checks/{id_}", response_model=MonitorCheckResponse)
async def get_monitor_check(monitor_id: UUID, id_: UUID):
    async with get_db() as db:
        return await MonitorCheckService(db).get_by_id(monitor_id, id_)


@monitor_check_router.put("/{monitor_id}/checks/{id_}", response_model=MonitorCheckResponse)
async def update_monitor_check(monitor_id: UUID, id_: UUID, data: UpdateMonitorCheck):
    async with get_db() as db:
        return await MonitorCheckService(db).update(monitor_id, id_, data)


@monitor_check_router.delete("/{monitor_id}/checks/{id_}", status_code=204)
async def delete_monitor_check(monitor_id: UUID, id_: UUID):
    async with get_db() as db:
        await MonitorCheckService(db).delete(monitor_id, id_)
