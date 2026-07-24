from datetime import datetime
from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import text

from app.dependencies.client_ip_provider import get_client_ip
from app.schemas import HealthResponse

from ....db.database import get_db

health_router = APIRouter()
logger = logging.getLogger("health")


@health_router.get("/api/core/health", tags=["Health"], response_model=HealthResponse)
async def health_check(
    request: Request, response: Response, client_ip: str = Depends(get_client_ip)
):
    try:
        database_alive = await _check_database_alive()

        if not database_alive:
            response.status_code = HTTPStatus.SERVICE_UNAVAILABLE

        return HealthResponse(
            client_ip=client_ip,
            server_ip=request.scope.get("server", ("unknown", 0))[0],
            current_date_time=datetime.now(),
            api_version=request.app.version,
            database_alive=database_alive,
            message="Core Running OK" if database_alive else "Database unavailable",
        )
    except Exception as e:
        logger.exception(f"[HEALTH_CHECK] -> {e}")
        raise


async def _check_database_alive() -> bool:
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))

        return True

    except Exception as e:
        logger.exception(f"[HEALTH CHECK] banco indisponível → {e}")
        return False
