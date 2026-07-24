from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.dependencies.authentication import auth_guard
from app.dependencies.rate_limit import rate_limited
from app.schemas import PaginatedResponse

from .incident_schema import (
    CreateIncident,
    IncidentResponse,
    IncidentSearchRequest,
    UpdateIncident,
)
from .incident_service import IncidentService, get_incident_service

incident_router = APIRouter(
    dependencies=[Depends(auth_guard)],
    route_class=rate_limited("100/minute"),
)


@incident_router.post("/{monitor_id}/", status_code=201, response_model=IncidentResponse)
async def create_incident(
    monitor_id: UUID,
    data: CreateIncident,
    service: IncidentService = Depends(get_incident_service),
):
    return await service.create(monitor_id, data)


@incident_router.get("/{monitor_id}/", response_model=PaginatedResponse[IncidentResponse])
async def search_incidents(
    monitor_id: UUID,
    filters: Annotated[IncidentSearchRequest, Query()],
    service: IncidentService = Depends(get_incident_service),
):
    return await service.search(monitor_id, filters)


@incident_router.get("/{monitor_id}/{id_}", response_model=IncidentResponse)
async def get_incident(
    monitor_id: UUID,
    id_: UUID,
    service: IncidentService = Depends(get_incident_service),
):
    return await service.get_by_id(monitor_id, id_)


@incident_router.put("/{monitor_id}/{id_}", response_model=IncidentResponse)
async def update_incident(
    monitor_id: UUID,
    id_: UUID,
    data: UpdateIncident,
    service: IncidentService = Depends(get_incident_service),
):
    return await service.update(monitor_id, id_, data)


@incident_router.delete("/{monitor_id}/{id_}", status_code=204)
async def delete_incident(
    monitor_id: UUID,
    id_: UUID,
    service: IncidentService = Depends(get_incident_service),
):
    await service.delete(monitor_id, id_)
