import logging

import redis.asyncio as redis

from ..core.config import settings

logger = logging.getLogger("redis")


class RedisClient:
    """Cliente Redis async da aplicação.

    Gerencia um único pool de conexões (criado no lifespan do ``main.py``) e
    expõe o client subjacente via ``self.client``. Sob ``scale: 3`` cada réplica
    tem seu próprio pool, mas todas apontam para a mesma instância do Redis.
    """

    def __init__(self, url: str):
        self._url = url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Abre o pool de conexões e valida com um ``PING``."""
        if self._client is not None:
            return

        self._client = redis.from_url(self._url, encoding="utf-8", decode_responses=True)
        await self._client.ping()
        logger.info("[REDIS] -> conectado")

    async def disconnect(self) -> None:
        """Encerra o pool de conexões."""
        if self._client is None:
            return

        await self._client.aclose()
        self._client = None
        logger.info("[REDIS] -> desconectado")

    @property
    def client(self) -> redis.Redis:
        """Retorna o client Redis. Requer ``connect()`` já executado."""
        if self._client is None:
            raise RuntimeError("Redis não inicializado. Chame connect() no lifespan.")

        return self._client


redis_client = RedisClient(settings.REDIS_URL)
