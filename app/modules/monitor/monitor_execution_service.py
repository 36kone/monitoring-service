import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...db.database import AsyncSessionLocal, get_db
from ..incident import IncidentService
from ..monitor import MonitorService
from ..monitor.health_checker import HealthChecker
from ..monitor_authentication.authentication_resolver import AuthenticationResolver
from ..monitor_authentication.monitor_authentication_service import (
    MonitorAuthenticationService,
)
from ..monitor_check import MonitorCheckService


class MonitorExecutionService:
    def __init__(self, session: AsyncSession):
        self._monitor_service = MonitorService(session)

    async def execute(self) -> None:
        monitors = await self._monitor_service.get_due()
        await asyncio.gather(*(self._execute_monitor(monitor.id) for monitor in monitors))

    async def _execute_monitor(self, monitor_id: UUID) -> None:
        async with AsyncSessionLocal() as session:
            monitor_service = MonitorService(session)
            monitor_check_service = MonitorCheckService(session)
            incident_service = IncidentService(session)
            authentication_service = MonitorAuthenticationService(session)

            monitor = await monitor_service.get_by_id(monitor_id)

            check = await HealthChecker(
                monitor, AuthenticationResolver(authentication_service)
            ).check()

            check = await monitor_check_service.create_from_result(check)

            await monitor_service.update_after_check(
                monitor,
                status=check.status,
                success=check.success,
                checked_at=check.checked_at,
            )

            await incident_service.process_check(
                monitor.id,
                success=check.success,
                checked_at=check.checked_at,
            )


async def run_monitor_jobs() -> None:
    async for session in get_db():
        service = MonitorExecutionService(session)
        await service.execute()
