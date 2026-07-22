import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db.database import get_db
from app.dependencies.authentication import auth_guard
from app.dependencies.rate_limit import rate_limited
from app.schemas import PaginatedResponse

from .monitor_schema import CreateMonitor, MonitorResponse, MonitorSearchRequest, UpdateMonitor
from .monitor_service import MonitorService

monitor_router = APIRouter(
    dependencies=[Depends(auth_guard)],
    route_class=rate_limited("100/minute"),
)
logger = logging.getLogger("monitors")


@monitor_router.post("/", status_code=201, response_model=MonitorResponse)
async def create_monitor(data: CreateMonitor):
    async with get_db() as db:
        return await MonitorService(db).create(data)


@monitor_router.get("/", response_model=PaginatedResponse[MonitorResponse])
async def search_monitors(
    filters: Annotated[MonitorSearchRequest, Query()],
):
    async with get_db() as db:
        return await MonitorService(db).search(filters)


@monitor_router.get("/{id_}", response_model=MonitorResponse)
async def get_monitor(id_: UUID):
    async with get_db() as db:
        return await MonitorService(db).get_by_id(id_)


@monitor_router.put("/{id_}", response_model=MonitorResponse)
async def update_monitor(id_: UUID, data: UpdateMonitor):
    async with get_db() as db:
        return await MonitorService(db).update(id_, data)


@monitor_router.delete("/{id_}", status_code=204)
async def delete_monitor(id_: UUID):
    async with get_db() as db:
        await MonitorService(db).delete(id_)
