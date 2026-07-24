from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.dependencies.exception_utils import ensure_or_404
from app.schemas import PaginatedResponse

from .monitor_enum import MonitorStatusEnum
from .monitor_model import Monitor
from .monitor_schema import (
    CreateMonitor,
    MonitorResponse,
    MonitorSearchRequest,
    UpdateMonitor,
)


class MonitorService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: CreateMonitor) -> Monitor:
        entity = Monitor(
            name=data.name.strip(),
            url=str(data.url),
            method=data.method,
            interval_seconds=data.interval_seconds,
            timeout_ms=data.timeout_ms,
            enabled=data.enabled,
        )
        self._session.add(entity)
        await self._session.commit()
        return await self.get_by_id(entity.id)

    async def get_all(self) -> list[Monitor]:
        return list((await self._session.scalars(select(Monitor))).all())

    async def get_due(self, now: datetime | None = None) -> list[Monitor]:
        now = now or datetime.now(UTC)
        query = select(Monitor).where(
            Monitor.enabled.is_(True),
            or_(Monitor.next_check_at.is_(None), Monitor.next_check_at <= now),
        )
        return list((await self._session.scalars(query)).all())

    async def update_after_check(
        self,
        monitor: Monitor,
        *,
        status: MonitorStatusEnum,
        success: bool,
        checked_at: datetime,
    ) -> Monitor:
        monitor.status = status
        monitor.last_checked_at = checked_at
        monitor.next_check_at = checked_at + timedelta(seconds=monitor.interval_seconds)

        if success:
            monitor.consecutive_successes += 1
            monitor.consecutive_failures = 0
        else:
            monitor.consecutive_failures += 1
            monitor.consecutive_successes = 0

        await self._session.commit()
        await self._session.refresh(monitor)
        return monitor

    async def search(self, filters: MonitorSearchRequest) -> PaginatedResponse[MonitorResponse]:
        query = select(Monitor)

        if filters.keyword:
            keyword = f"%{filters.keyword.strip()}%"
            query = query.where(or_(Monitor.name.ilike(keyword), Monitor.url.ilike(keyword)))
        if filters.enabled is not None:
            query = query.where(Monitor.enabled == filters.enabled)
        if filters.status is not None:
            query = query.where(Monitor.status == filters.status)

        total = await self._session.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = (
            query.order_by(Monitor.name.asc())
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        )
        result = await self._session.execute(query)
        items = result.scalars().all()

        return PaginatedResponse.create(
            total=total,
            page=filters.page,
            size=filters.size,
            items=[MonitorResponse.model_validate(item, from_attributes=True) for item in items],
        )

    async def get_by_id(self, id_: UUID) -> Monitor:
        entity = await self._session.scalar(select(Monitor).where(Monitor.id == id_))
        return ensure_or_404(entity, "Monitor not found")

    async def update(self, id_: UUID, data: UpdateMonitor) -> Monitor:
        entity = await self.get_by_id(id_)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, str(value) if field == "url" else value)
        await self._session.commit()
        return await self.get_by_id(entity.id)

    async def delete(self, id_: UUID) -> None:
        entity = await self.get_by_id(id_)
        await self._session.delete(entity)
        await self._session.commit()


def get_monitor_service(session: AsyncSession = Depends(get_db)) -> MonitorService:
    return MonitorService(session)
