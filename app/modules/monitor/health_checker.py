from datetime import UTC, datetime
from time import perf_counter

import httpx

from ...dependencies.client import AsyncClient
from ..monitor_authentication.authentication_resolver import AuthenticationResolver
from ..monitor_check import MonitorCheck
from .monitor_enum import MonitorStatusEnum
from .monitor_model import Monitor


class HealthChecker:
    def __init__(
        self, monitor: Monitor, authentication: AuthenticationResolver | None = None
    ) -> None:
        self._client = AsyncClient(monitor.timeout_ms / 1000)
        self._monitor = monitor
        self._authentication = authentication

    async def check(self) -> MonitorCheck:
        checked_at = datetime.now(UTC)
        started_at = perf_counter()

        try:
            request_auth = (
                await self._authentication.resolve(self._monitor.id)
                if self._authentication
                else None
            )
            result = await self._request(request_auth)
            if result.status_code == 401 and request_auth and request_auth.retry_on_unauthorized:
                await self._authentication.invalidate(self._monitor.id)
                request_auth = await self._authentication.resolve(self._monitor.id, force=True)
                result = await self._request(request_auth)
        except httpx.TimeoutException as error:
            return self._failure(checked_at, started_at, str(error) or "Request timed out", True)
        except httpx.RequestError as error:
            return self._failure(checked_at, started_at, str(error) or "Request failed")
        except (ValueError, KeyError, httpx.HTTPStatusError) as error:
            return self._failure(checked_at, started_at, str(error) or "Authentication failed")

        success = result.is_success
        status = MonitorStatusEnum.UP if success else MonitorStatusEnum.DEGRADED
        return MonitorCheck(
            monitor_id=self._monitor.id,
            status=status,
            status_code=result.status_code,
            success=success,
            latency_ms=round((perf_counter() - started_at) * 1000),
            response_body=self._response_body(result),
            checked_at=checked_at,
        )

    async def _request(self, request_auth):
        headers = {**(self._monitor.request_headers or {})}
        if request_auth:
            headers.update(request_auth.headers)
        return await self._client.request(
            self._monitor.method,
            self._monitor.url,
            headers=headers or None,
            auth=request_auth.auth if request_auth else None,
            json=self._monitor.request_body,
        )

    def _failure(self, checked_at, started_at, error: str, timed_out: bool = False) -> MonitorCheck:
        return MonitorCheck(
            monitor_id=self._monitor.id,
            status=MonitorStatusEnum.DOWN,
            success=False,
            latency_ms=round((perf_counter() - started_at) * 1000),
            error=error[:1000],
            timed_out=timed_out,
            checked_at=checked_at,
        )

    @staticmethod
    def _response_body(response):
        if not response.text:
            return None
        try:
            import json

            return json.loads(response.text[:10000])
        except (TypeError, ValueError):
            return response.text[:10000]
