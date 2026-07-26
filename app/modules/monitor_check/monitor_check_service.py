from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies.exception_utils import ensure_or_404
from app.schemas import PaginatedResponse

from ..monitor.monitor_model import Monitor
from .monitor_check_model import MonitorCheck
from .monitor_check_schema import (
    CreateMonitorCheck,
    MonitorCheckResponse,
    MonitorCheckSearchRequest,
    UpdateMonitorCheck,
)


class MonitorCheckService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def _get_monitor(self, monitor_id: UUID) -> Monitor:
        monitor = await self._session.scalar(select(Monitor).where(Monitor.id == monitor_id))
        return ensure_or_404(monitor, "Monitor not found")

    async def create(self, monitor_id: UUID, data: CreateMonitorCheck) -> MonitorCheck:
        await self._get_monitor(monitor_id)
        entity = MonitorCheck(
            monitor_id=monitor_id,
            status=data.status,
            status_code=data.status_code,
            success=data.success,
            latency_ms=data.latency_ms,
            error=data.error,
            response_body=None if data.response_body == "" else data.response_body,
            timed_out=data.timed_out,
        )
        self._session.add(entity)
        await self._session.commit()
        return await self.get_by_id(monitor_id, entity.id)

    async def create_from_result(self, check: MonitorCheck) -> MonitorCheck:
        await self._get_monitor(check.monitor_id)
        if check.response_body == "":
            check.response_body = None
        self._session.add(check)
        await self._session.commit()
        return await self.get_by_id(check.monitor_id, check.id)

    async def search(
        self, monitor_id: UUID, filters: MonitorCheckSearchRequest
    ) -> PaginatedResponse[MonitorCheckResponse]:
        await self._get_monitor(monitor_id)
        query = select(MonitorCheck).where(MonitorCheck.monitor_id == monitor_id)

        if filters.status is not None:
            query = query.where(MonitorCheck.status == filters.status)
        if filters.success is not None:
            query = query.where(MonitorCheck.success == filters.success)

        total = await self._session.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = (
            query.order_by(MonitorCheck.checked_at.desc())
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        )
        result = await self._session.execute(query)
        items = result.scalars().all()

        return PaginatedResponse.create(
            total=total,
            page=filters.page,
            size=filters.size,
            items=[
                MonitorCheckResponse.model_validate(item, from_attributes=True) for item in items
            ],
        )

    async def get_by_id(self, monitor_id: UUID, id_: UUID) -> MonitorCheck:
        await self._get_monitor(monitor_id)
        entity = await self._session.scalar(
            select(MonitorCheck).where(
                MonitorCheck.id == id_, MonitorCheck.monitor_id == monitor_id
            )
        )
        return ensure_or_404(entity, "Monitor check not found")

    async def update(self, monitor_id: UUID, id_: UUID, data: UpdateMonitorCheck) -> MonitorCheck:
        entity = await self.get_by_id(monitor_id, id_)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, None if field == "response_body" and value == "" else value)
        await self._session.commit()
        return await self.get_by_id(monitor_id, entity.id)

    async def delete(self, monitor_id: UUID, id_: UUID) -> None:
        entity = await self.get_by_id(monitor_id, id_)
        await self._session.delete(entity)
        await self._session.commit()


def get_monitor_check_service(
    session: AsyncSession = Depends(get_db),
) -> MonitorCheckService:
    return MonitorCheckService(session)
