from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
import redis.asyncio as redis

# TTL padrão dos dashboards (agregações pesadas, toleram defasagem).
DASHBOARD_CACHE_TTL: int = 60 * 20  # 20 minutos
REAL_TIME_CACHE_TTL: int = 60 * 20  # 20 minutos


def init_cache(redis_url: str | None = None) -> redis.Redis | None:
    """Inicializa o cache da aplicação.

    Com uma ``redis_url`` (produção/lifespan), usa ``RedisBackend`` para que as 3
    réplicas compartilhem o mesmo cache. Sem URL (ex.: testes, que não sobem o
    lifespan), cai no ``InMemoryBackend`` por processo.

    Usa uma conexão dedicada com ``decode_responses=False``: o ``JsonCoder`` do
    fastapi-cache grava/lê bytes, então NÃO dá para reaproveitar o client do
    pub/sub (que exige ``decode_responses=True``). Retorna o client para o lifespan
    fechar no shutdown; retorna ``None`` no modo InMemory.
    """
    if redis_url is None:
        FastAPICache.init(InMemoryBackend(), prefix="impacto-cache")
        return None

    cache_redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=False)
    FastAPICache.init(RedisBackend(cache_redis), prefix="impacto-cache")

    return cache_redis
