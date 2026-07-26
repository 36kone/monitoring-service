from typing import Any

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

from .dashboard_schema import DashboardHomeResponse


class DashboardService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_home(self) -> DashboardHomeResponse:
        payload = await self._fetch_home_payload()
        return self._build_home_response(payload)

    async def _fetch_home_payload(self) -> Any:
        result = await self._session.execute(self._home_query())
        return result.scalar_one()

    @staticmethod
    def _build_home_response(payload: Any) -> DashboardHomeResponse:
        return DashboardHomeResponse.model_validate(payload)

    @staticmethod
    def _home_query():
        return text(
            """
            WITH recent_checks AS (
                SELECT DISTINCT ON (mc.monitor_id)
                    mc.monitor_id,
                    mc.latency_ms,
                    mc.checked_at
                FROM monitor_checks mc
                ORDER BY mc.monitor_id, mc.checked_at DESC
            ),
            check_stats AS (
                SELECT
                    COALESCE(100.0 * AVG(CASE WHEN mc.success THEN 1.0 ELSE 0.0 END), 100.0) AS overall_uptime,
                    COALESCE(AVG(mc.latency_ms) FILTER (WHERE mc.latency_ms IS NOT NULL), 0.0) AS average_latency_ms
                FROM monitor_checks mc
                WHERE mc.checked_at >= NOW() - INTERVAL '30 days'
            ),
            daily_uptime AS (
                SELECT
                    TO_CHAR(DATE_TRUNC('day', mc.checked_at), 'YYYY-MM-DD') AS date,
                    ROUND((100.0 * AVG(CASE WHEN mc.success THEN 1.0 ELSE 0.0 END))::numeric, 2) AS uptime
                FROM monitor_checks mc
                WHERE mc.checked_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE_TRUNC('day', mc.checked_at)
                ORDER BY DATE_TRUNC('day', mc.checked_at)
            ),
            monitor_data AS (
                SELECT COALESCE(JSON_AGG(JSON_BUILD_OBJECT(
                    'id', m.id,
                    'name', m.name,
                    'url', m.url,
                    'method', m.method,
                    'status', m.status,
                    'enabled', m.enabled,
                    'interval_seconds', m.interval_seconds,
                    'last_checked_at', rc.checked_at,
                    'last_latency_ms', rc.latency_ms
                ) ORDER BY m.name), '[]'::json) AS items
                FROM monitors m
                LEFT JOIN recent_checks rc ON rc.monitor_id = m.id
            ),
            incident_data AS (
                SELECT COALESCE(JSON_AGG(JSON_BUILD_OBJECT(
                    'id', i.id,
                    'monitor_id', i.monitor_id,
                    'monitor_name', m.name,
                    'status', i.status,
                    'started_at', i.started_at,
                    'resolved_at', i.resolved_at,
                    'duration_seconds', i.duration_seconds
                ) ORDER BY i.started_at DESC), '[]'::json) AS items
                FROM incidents i
                JOIN monitors m ON m.id = i.monitor_id
                WHERE i.started_at >= NOW() - INTERVAL '30 days'
            )
            SELECT JSON_BUILD_OBJECT(
                'overall_uptime', cs.overall_uptime,
                'average_latency_ms', cs.average_latency_ms,
                'active_monitors', COUNT(DISTINCT m.id) FILTER (WHERE m.enabled),
                'operational_monitors', COUNT(DISTINCT m.id) FILTER (WHERE m.enabled AND m.status = 'up'),
                'open_incidents', COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'open'),
                'uptime_series', COALESCE((SELECT JSON_AGG(du ORDER BY du.date) FROM daily_uptime du), '[]'::json),
                'recent_incidents', (SELECT items FROM incident_data),
                'monitors', (SELECT items FROM monitor_data)
            )
            FROM check_stats cs
            LEFT JOIN monitors m ON TRUE
            LEFT JOIN incidents i ON i.monitor_id = m.id
            GROUP BY cs.overall_uptime, cs.average_latency_ms
            """
        )


def get_dashboard_service(session: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(session)
