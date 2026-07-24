import httpx


class AsyncClient:
    def __init__(self, timeout: float = 15) -> None:
        self._timeout = timeout

    async def request(self, method: str, path: str, *, json=None, params=None) -> httpx.Response:
        async with httpx.AsyncClient() as http:
            return await http.request(method, path, json=json, params=params, timeout=self._timeout)
