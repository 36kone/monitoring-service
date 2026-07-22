from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.exception_utils import ensure_or_404
from app.schemas import PaginatedResponse

from ..monitor.monitor_model import Monitor
from .incident_model import Incident
from .incident_schema import CreateIncident, IncidentResponse, IncidentSearchRequest, UpdateIncident


class IncidentService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def _get_monitor(self, monitor_id: UUID) -> Monitor:
        monitor = await self._session.scalar(select(Monitor).where(Monitor.id == monitor_id))
        return ensure_or_404(monitor, "Monitor not found")

    async def create(self, monitor_id: UUID, data: CreateIncident) -> Incident:
        await self._get_monitor(monitor_id)
        entity = Incident(
            monitor_id=monitor_id,
            status=data.status,
            started_at=data.started_at,
            resolved_at=data.resolved_at,
            duration_seconds=data.duration_seconds,
        )
        self._session.add(entity)
        await self._session.commit()
        return await self.get_by_id(monitor_id, entity.id)

    async def search(
        self, monitor_id: UUID, filters: IncidentSearchRequest
    ) -> PaginatedResponse[IncidentResponse]:
        await self._get_monitor(monitor_id)
        query = select(Incident).where(Incident.monitor_id == monitor_id)

        if filters.status is not None:
            query = query.where(Incident.status == filters.status)

        total = await self._session.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = (
            query.order_by(Incident.started_at.desc())
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        )
        result = await self._session.execute(query)
        items = result.scalars().all()

        return PaginatedResponse.create(
            total=total,
            page=filters.page,
            size=filters.size,
            items=[IncidentResponse.model_validate(item, from_attributes=True) for item in items],
        )

    async def get_by_id(self, monitor_id: UUID, id_: UUID) -> Incident:
        await self._get_monitor(monitor_id)
        entity = await self._session.scalar(
            select(Incident).where(Incident.id == id_, Incident.monitor_id == monitor_id)
        )
        return ensure_or_404(entity, "Incident not found")

    async def update(self, monitor_id: UUID, id_: UUID, data: UpdateIncident) -> Incident:
        entity = await self.get_by_id(monitor_id, id_)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        await self._session.commit()
        return await self.get_by_id(monitor_id, entity.id)

    async def delete(self, monitor_id: UUID, id_: UUID) -> None:
        entity = await self.get_by_id(monitor_id, id_)
        await self._session.delete(entity)
        await self._session.commit()
