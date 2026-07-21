from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import init_cache
from app.core.config import settings
from app.redis.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.connect()
    cache_redis = init_cache(settings.REDIS_URL)

    try:
        yield
    finally:
        if cache_redis is not None:
            await cache_redis.aclose()
        await redis_client.disconnect()
