import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.authentication import auth_guard
from app.dependencies.rate_limit import rate_limited
from app.schemas import PaginatedResponse

from .monitor_schema import CreateMonitor, MonitorResponse, MonitorSearchRequest, UpdateMonitor
from .monitor_service import MonitorService, get_monitor_service

monitor_router = APIRouter(
    dependencies=[Depends(auth_guard)],
    route_class=rate_limited("100/minute"),
)
logger = logging.getLogger("monitors")


@monitor_router.post("/", status_code=201, response_model=MonitorResponse)
async def create_monitor(
    data: CreateMonitor,
    service: MonitorService = Depends(get_monitor_service),
):
    return await service.create(data)


@monitor_router.get("/", response_model=PaginatedResponse[MonitorResponse])
async def search_monitors(
    filters: Annotated[MonitorSearchRequest, Query()],
    service: MonitorService = Depends(get_monitor_service),
):
    return await service.search(filters)


@monitor_router.get("/{id_}", response_model=MonitorResponse)
async def get_monitor(
    id_: UUID,
    service: MonitorService = Depends(get_monitor_service),
):
    return await service.get_by_id(id_)


@monitor_router.put("/{id_}", response_model=MonitorResponse)
async def update_monitor(
    id_: UUID,
    data: UpdateMonitor,
    service: MonitorService = Depends(get_monitor_service),
):
    return await service.update(id_, data)


@monitor_router.delete("/{id_}", status_code=204)
async def delete_monitor(
    id_: UUID,
    service: MonitorService = Depends(get_monitor_service),
):
    await service.delete(id_)
