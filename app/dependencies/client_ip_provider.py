from fastapi import Request


class ClientIP:
    """
    Dependência para capturar o IP real do cliente, considerando proxies como Traefik ou Nginx.
    """

    def __call__(self, request: Request) -> str:
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # O primeiro IP na lista é o cliente original
            return x_forwarded_for.split(",")[0].strip()

        return request.headers.get("X-Real-IP") or (
            request.client.host if request.client else "unknown"
        )


get_client_ip = ClientIP()
