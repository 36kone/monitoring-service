from collections.abc import Callable
import inspect
from typing import Any

from fastapi import Request
from fastapi.routing import APIRoute

from app.dependencies.limiter import limiter

_LIMIT_ATTR = "__rate_limit_value__"
_EXEMPT_ATTR = "__rate_limit_exempt__"


class RateLimitedRoute(APIRoute):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.default_limit: str = kwargs.pop("default_limit", "300/minute")
        self._cached_handler: Callable | None = None
        super().__init__(*args, **kwargs)

    def get_route_handler(self):
        # Se já gerou 1 vez, reutiliza (singleton-like por rota)
        if self._cached_handler is not None:
            return self._cached_handler

        original_handler = super().get_route_handler()

        endpoint = self.endpoint
        if getattr(endpoint, _EXEMPT_ATTR, False):
            self._cached_handler = original_handler
            return original_handler

        limit_value = getattr(endpoint, _LIMIT_ATTR, None) or self.default_limit

        # Gera um scope único por rota para evitar colisão de buckets
        methods = "_".join(sorted(self.methods or [])) or "ANY"
        scope = f"rl_{methods}{self.path_format}".replace("/", "").replace("{", "").replace("}", "")

        async def scoped_handler(request: Request):
            # Ignora rate limit para requisições OPTIONS (CORS Preflight)
            if request.method == "OPTIONS":
                result = original_handler(request)
                if inspect.isawaitable(result):
                    return await result
                return result

            result = original_handler(request)
            if inspect.isawaitable(result):
                return await result
            return result

        # Define um nome único para o SlowAPI identificar esta rota individualmente
        scoped_handler.__name__ = scope  # type: ignore
        limited_handler = limiter.limit(limit_value)(scoped_handler)

        async def handler(request: Request):
            # passa request como keyword pra slowapi pegar 100%
            result = limited_handler(request=request)
            if inspect.isawaitable(result):
                return await result
            return result

        self._cached_handler = handler
        return handler


def rate_limited(default_limit: str) -> type[RateLimitedRoute]:
    """Cria uma subclasse de rota com o limite padrão embutido.

    Retorna uma classe (não instância nem partial) para satisfazer o
    parâmetro `route_class: type[APIRoute]` do `APIRouter`.
    """

    class _ConfiguredRateLimitedRoute(RateLimitedRoute):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("default_limit", default_limit)
            super().__init__(*args, **kwargs)

    return _ConfiguredRateLimitedRoute


def limit(limit_value: str):
    """
    Decorator para sobrescrever o limite padrão de uma rota específica.
    Uso: @limit("10/minute")
    Caso queira limitar apenas 1 endpoint, use: @limiter.limit("5/minute")
    """

    def decorator(func: Callable):
        setattr(func, _LIMIT_ATTR, limit_value)
        return func

    return decorator


def exempt(func: Callable):
    """
    Decorator para isentar uma rota específica do rate limit.
    Uso: @exempt
    """
    setattr(func, _EXEMPT_ATTR, True)
    return func
