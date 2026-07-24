import asyncio
from collections.abc import AsyncIterator
import socket

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.main import app
from app.modules.incident import Incident, IncidentStatusEnum
from app.modules.monitor import Monitor, MonitorStatusEnum
from app.modules.monitor.monitor_execution_service import run_monitor_jobs
from app.modules.monitor_check import MonitorCheck


@pytest_asyncio.fixture
async def running_api() -> AsyncIterator[str]:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 0))
    server_socket.listen(128)
    server_socket.setblocking(False)

    port = server_socket.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            log_level="error",
            lifespan="off",
        )
    )
    server_task = asyncio.create_task(server.serve(sockets=[server_socket]))

    try:
        async with asyncio.timeout(5):
            while not server.started:
                if server_task.done():
                    await server_task
                await asyncio.sleep(0.01)

        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await server_task


async def _create_monitor(
    db_session: AsyncSession,
    *,
    url: str,
    interval_seconds: int = 60,
) -> Monitor:
    monitor = Monitor(
        name="Background test monitor",
        url=url,
        method="GET",
        interval_seconds=interval_seconds,
        timeout_ms=5000,
        enabled=True,
    )
    db_session.add(monitor)
    await db_session.commit()
    await db_session.refresh(monitor)
    return monitor


@pytest.mark.asyncio
async def test_background_checks_application_health(
    db_session: AsyncSession,
    running_api: str,
) -> None:
    monitor = await _create_monitor(
        db_session,
        url=f"{running_api}/api/health",
        interval_seconds=60,
    )

    await run_monitor_jobs()

    await db_session.refresh(monitor)
    checks = list(
        (
            await db_session.scalars(
                select(MonitorCheck)
                .where(MonitorCheck.monitor_id == monitor.id)
                .order_by(MonitorCheck.checked_at.asc())
            )
        ).all()
    )
    incident = await db_session.scalar(select(Incident).where(Incident.monitor_id == monitor.id))

    assert len(checks) == 1
    assert checks[0].success is True
    assert checks[0].status is MonitorStatusEnum.UP
    assert checks[0].status_code == 200
    assert checks[0].latency_ms is not None
    assert monitor.status is MonitorStatusEnum.UP
    assert monitor.next_check_at is not None
    assert incident is None

    monitor.url = "http://127.0.0.1:1/health"
    monitor.next_check_at = None
    await db_session.commit()
    await run_monitor_jobs()

    await db_session.refresh(monitor)
    incident = await db_session.scalar(
        select(Incident).where(
            Incident.monitor_id == monitor.id,
            Incident.status == IncidentStatusEnum.OPEN,
        )
    )
    assert monitor.status is MonitorStatusEnum.DOWN
    assert incident is not None

    monitor.url = f"{running_api}/api/health"
    monitor.next_check_at = None
    await db_session.commit()
    await run_monitor_jobs()

    await db_session.refresh(monitor)
    incident = await db_session.scalar(select(Incident).where(Incident.monitor_id == monitor.id))
    assert incident is not None
    await db_session.refresh(incident)
    checks = list(
        (
            await db_session.scalars(
                select(MonitorCheck)
                .where(MonitorCheck.monitor_id == monitor.id)
                .order_by(MonitorCheck.checked_at.asc())
            )
        ).all()
    )

    assert len(checks) == 3
    assert checks[-1].success is True
    assert monitor.status is MonitorStatusEnum.UP
    assert incident.status == IncidentStatusEnum.RESOLVED
    assert incident.resolved_at is not None
