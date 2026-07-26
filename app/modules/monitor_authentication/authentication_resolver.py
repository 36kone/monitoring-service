import base64
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import json
import time
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx

from app.core.credentials_crypto import decrypt_credentials, encrypt_credentials
from app.redis.redis import redis_client

from .login_body_type import LoginBodyType
from .monitor_authentication_enum import MonitorAuthenticationTypeEnum
from .monitor_authentication_service import MonitorAuthenticationService


@dataclass
class ResolvedRequestAuthentication:
    headers: dict[str, str] = field(default_factory=dict)
    auth: httpx.BasicAuth | None = None
    retry_on_unauthorized: bool = False


class AuthenticationResolver:
    def __init__(self, service: MonitorAuthenticationService):
        self._service = service

    async def resolve(self, monitor_id: UUID, *, force: bool = False) -> ResolvedRequestAuthentication:
        entity, credentials = await self._service.get_decrypted(monitor_id)
        if entity is None:
            return ResolvedRequestAuthentication()
        auth_type = MonitorAuthenticationTypeEnum(entity.auth_type)
        if auth_type is MonitorAuthenticationTypeEnum.NONE:
            return ResolvedRequestAuthentication()
        if auth_type is MonitorAuthenticationTypeEnum.API_KEY:
            return ResolvedRequestAuthentication(
                headers={credentials.get("header_name", "X-API-Key"): credentials["api_key"]}
            )
        if auth_type is MonitorAuthenticationTypeEnum.BEARER_TOKEN:
            return ResolvedRequestAuthentication(
                headers={
                    entity.authorization_header: f"{entity.authorization_scheme} {credentials['token']}".strip()
                }
            )
        if auth_type is MonitorAuthenticationTypeEnum.BASIC:
            return ResolvedRequestAuthentication(
                auth=httpx.BasicAuth(credentials["username"], credentials["password"])
            )

        token, _expires_at = await self._get_dynamic_token(entity, credentials, force=force)
        value = f"{entity.authorization_scheme} {token}".strip()
        return ResolvedRequestAuthentication(
            headers={entity.authorization_header: value}, retry_on_unauthorized=True
        )

    async def invalidate(self, monitor_id: UUID) -> None:
        client = self._redis()
        if client is not None:
            await client.delete(self._cache_key(monitor_id))

    async def _get_dynamic_token(self, entity, credentials: dict, *, force: bool) -> tuple[str, datetime]:
        if not force:
            cached = await self._read_token(entity.monitor_id)
            if cached:
                return cached

        client = self._redis()
        lock_key = self._lock_key(entity.monitor_id)
        lock_value = str(time.time_ns())
        acquired = False
        if client is not None:
            acquired = bool(await client.set(lock_key, lock_value, nx=True, ex=30))
            if not acquired:
                for _ in range(10):
                    await self._sleep()
                    cached = await self._read_token(entity.monitor_id)
                    if cached:
                        return cached
                acquired = bool(await client.set(lock_key, lock_value, nx=True, ex=30))

        try:
            token, expires_at = await self._login(entity, credentials)
            await self._write_token(entity.monitor_id, token, expires_at)
            return token, expires_at
        finally:
            if client is not None and acquired:
                await client.delete(lock_key)

    async def _login(self, entity, credentials: dict) -> tuple[str, datetime]:
        body = credentials.get("login_body") or {}
        request_options: dict[str, Any] = {"headers": credentials.get("login_headers"), "timeout": 10}
        if entity.login_body_type == LoginBodyType.JSON:
            request_options["json"] = body
        elif entity.login_body_type == LoginBodyType.FORM_URLENCODED:
            request_options["content"] = urlencode(body)
            request_options["headers"] = {
                **(request_options["headers"] or {}),
                "Content-Type": "application/x-www-form-urlencoded",
            }
        else:
            request_options["files"] = {key: (None, str(value)) for key, value in body.items()}
        async with httpx.AsyncClient() as client:
            response = await client.request(
                entity.login_method or "POST",
                entity.login_url,
                **request_options,
            )
        response.raise_for_status()
        payload = response.json()
        token = self._path(payload, entity.token_json_path)
        if not isinstance(token, str) or not token:
            raise ValueError("Authentication token was not found")
        expires_at = self._expiration(entity, payload, token)
        return token, expires_at

    async def _read_token(self, monitor_id: UUID) -> tuple[str, datetime] | None:
        client = self._redis()
        if client is None:
            return None
        raw = await client.get(self._cache_key(monitor_id))
        if not raw:
            return None
        try:
            value = json.loads(raw)
            credentials = decrypt_credentials(value["encrypted"], value["nonce"])
            expires_at = datetime.fromisoformat(value["expires_at"])
            if expires_at <= datetime.now(UTC) + timedelta(seconds=int(value["skew"])):
                return None
            return credentials["token"], expires_at
        except (KeyError, TypeError, ValueError):
            return None

    async def _write_token(self, monitor_id: UUID, token: str, expires_at: datetime) -> None:
        client = self._redis()
        if client is None:
            return
        encrypted, nonce = encrypt_credentials({"token": token})
        ttl = max(1, int((expires_at - datetime.now(UTC)).total_seconds()))
        await client.set(
            self._cache_key(monitor_id),
            json.dumps({"encrypted": encrypted, "nonce": nonce, "expires_at": expires_at.isoformat(), "skew": 60}),
            ex=ttl,
        )

    @staticmethod
    def _expiration(entity, payload: dict, token: str) -> datetime:
        now = datetime.now(UTC)
        value = AuthenticationResolver._path(payload, entity.expires_at_json_path)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        if value is None:
            value = AuthenticationResolver._path(payload, entity.expires_in_json_path)
        if isinstance(value, (int, float)):
            return now + timedelta(seconds=value)
        try:
            encoded = token.split(".")[1]
            decoded = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            if isinstance(decoded.get("exp"), (int, float)):
                return datetime.fromtimestamp(decoded["exp"], UTC)
        except (IndexError, ValueError, TypeError, json.JSONDecodeError):
            pass
        return now + timedelta(minutes=5)

    @staticmethod
    def _path(value: Any, path: str | None) -> Any:
        if not path:
            return None
        current = value
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    @staticmethod
    def _redis():
        try:
            return redis_client.client
        except RuntimeError:
            return None

    @staticmethod
    async def _sleep():
        import asyncio

        await asyncio.sleep(0.05)

    @staticmethod
    def _cache_key(monitor_id: UUID) -> str:
        return f"monitor:{monitor_id}:auth:token"

    @staticmethod
    def _lock_key(monitor_id: UUID) -> str:
        return f"monitor:{monitor_id}:auth:lock"
