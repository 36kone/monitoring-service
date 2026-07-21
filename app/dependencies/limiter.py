from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.dependencies.client_ip_provider import get_client_ip

limiter = Limiter(key_func=get_client_ip)


def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> Response:
    client_ip = get_client_ip(request)

    response = JSONResponse(
        content={
            "error": f"Rate limit exceeded: {exc.detail} for {client_ip}",
        },
        status_code=429,
    )

    return response
