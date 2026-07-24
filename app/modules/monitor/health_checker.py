from datetime import UTC, datetime
from time import perf_counter

import httpx

from ...dependencies.client import AsyncClient
from ..monitor_check import MonitorCheck
from .monitor_enum import MonitorStatusEnum
from .monitor_model import Monitor


class HealthChecker:
    def __init__(self, monitor: Monitor) -> None:
        self._client = AsyncClient(monitor.timeout_ms / 1000)
        self._monitor = monitor

    async def check(self) -> MonitorCheck:
        checked_at = datetime.now(UTC)
        started_at = perf_counter()

        try:
            result = await self._client.request(self._monitor.method, self._monitor.url)
        except httpx.TimeoutException as error:
            latency_ms = round((perf_counter() - started_at) * 1000)
            return MonitorCheck(
                monitor_id=self._monitor.id,
                status=MonitorStatusEnum.DOWN,
                success=False,
                latency_ms=latency_ms,
                error=str(error) or "Request timed out",
                timed_out=True,
                checked_at=checked_at,
            )
        except httpx.RequestError as error:
            latency_ms = round((perf_counter() - started_at) * 1000)
            return MonitorCheck(
                monitor_id=self._monitor.id,
                status=MonitorStatusEnum.DOWN,
                success=False,
                latency_ms=latency_ms,
                error=str(error) or "Request failed",
                checked_at=checked_at,
            )

        success = result.is_success
        status = MonitorStatusEnum.UP if success else MonitorStatusEnum.DEGRADED
        return MonitorCheck(
            monitor_id=self._monitor.id,
            status=status,
            status_code=result.status_code,
            success=success,
            latency_ms=round((perf_counter() - started_at) * 1000),
            checked_at=checked_at,
        )
