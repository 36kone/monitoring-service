from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies.authentication import auth_guard
from app.dependencies.rate_limit import rate_limited

from .monitor_authentication_schema import (
    CreateMonitorAuthentication,
    MonitorAuthenticationResponse,
)
from .monitor_authentication_service import (
    MonitorAuthenticationService,
    get_monitor_authentication_service,
)

monitor_authentication_router = APIRouter(
    dependencies=[Depends(auth_guard)], route_class=rate_limited("100/minute")
)


@monitor_authentication_router.get(
    "/{monitor_id}/authentication", response_model=MonitorAuthenticationResponse
)
async def get_authentication(
    monitor_id: UUID,
    service: Annotated[MonitorAuthenticationService, Depends(get_monitor_authentication_service)],
):
    return await service.get_by_monitor_id(monitor_id)


@monitor_authentication_router.put(
    "/{monitor_id}/authentication", response_model=MonitorAuthenticationResponse
)
async def update_authentication(
    monitor_id: UUID,
    data: CreateMonitorAuthentication,
    service: Annotated[MonitorAuthenticationService, Depends(get_monitor_authentication_service)],
):
    return await service.create_or_update(monitor_id, data)


@monitor_authentication_router.delete("/{monitor_id}/authentication", status_code=204)
async def delete_authentication(
    monitor_id: UUID,
    service: Annotated[MonitorAuthenticationService, Depends(get_monitor_authentication_service)],
):
    await service.delete(monitor_id)
