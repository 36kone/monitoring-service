import httpx


class AsyncClient:
    def __init__(self, timeout: float = 15) -> None:
        self._timeout = timeout

    async def request(
        self,
        method: str,
        path: str,
        *,
        json=None,
        params=None,
        headers=None,
        auth=None,
        content=None,
        files=None,
    ) -> httpx.Response:
        async with httpx.AsyncClient() as http:
            return await http.request(
                method,
                path,
                json=json,
                params=params,
                headers=headers,
                auth=auth,
                content=content,
                files=files,
                timeout=self._timeout,
            )
