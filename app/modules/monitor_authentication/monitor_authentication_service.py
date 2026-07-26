from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credentials_crypto import decrypt_credentials, encrypt_credentials
from app.db.database import get_db
from app.dependencies.exception_utils import ensure_or_404
from app.modules.monitor.monitor_model import Monitor

from .monitor_authentication_enum import MonitorAuthenticationTypeEnum
from .monitor_authentication_model import MonitorAuthentication
from .monitor_authentication_schema import (
    CreateMonitorAuthentication,
    MonitorAuthenticationResponse,
)


class MonitorAuthenticationService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_monitor_id(self, monitor_id: UUID) -> MonitorAuthenticationResponse:
        entity = await self._get_entity(monitor_id)
        return self._public_response(entity)

    async def get_decrypted(self, monitor_id: UUID) -> tuple[MonitorAuthentication | None, dict]:
        entity = await self._session.scalar(
            select(MonitorAuthentication).where(MonitorAuthentication.monitor_id == monitor_id)
        )
        if entity is None:
            return None, {}
        if entity.auth_type == MonitorAuthenticationTypeEnum.NONE:
            return entity, {}
        if not entity.encrypted_credentials or not entity.nonce:
            return entity, {}
        return entity, decrypt_credentials(entity.encrypted_credentials, entity.nonce)

    async def create_or_update(
        self, monitor_id: UUID, data: CreateMonitorAuthentication
    ) -> MonitorAuthenticationResponse:
        await self._ensure_monitor(monitor_id)
        entity = await self._session.scalar(
            select(MonitorAuthentication).where(MonitorAuthentication.monitor_id == monitor_id)
        )
        credentials = data.credentials.model_dump(exclude_none=True)
        encrypted, nonce = encrypt_credentials(credentials) if credentials else (None, None)
        if entity is None:
            entity = MonitorAuthentication(monitor_id=monitor_id)
            self._session.add(entity)

        for field, value in self._metadata(data).items():
            setattr(entity, field, value)
        entity.encrypted_credentials = encrypted
        entity.nonce = nonce
        await self._session.commit()
        await self._session.refresh(entity)
        return self._public_response(entity)

    async def delete(self, monitor_id: UUID) -> None:
        await self._ensure_monitor(monitor_id)
        await self._session.execute(
            delete(MonitorAuthentication).where(MonitorAuthentication.monitor_id == monitor_id)
        )
        await self._session.commit()

    async def _get_entity(self, monitor_id: UUID) -> MonitorAuthentication:
        entity = await self._session.scalar(
            select(MonitorAuthentication).where(MonitorAuthentication.monitor_id == monitor_id)
        )
        return ensure_or_404(entity, "Monitor authentication not found")

    async def _ensure_monitor(self, monitor_id: UUID) -> Monitor:
        monitor = await self._session.scalar(select(Monitor).where(Monitor.id == monitor_id))
        return ensure_or_404(monitor, "Monitor not found")

    @staticmethod
    def _metadata(data: CreateMonitorAuthentication) -> dict:
        return {
            "auth_type": data.auth_type,
            "login_url": str(data.login_url) if data.login_url else None,
            "login_method": data.login_method.upper(),
            "login_body_type": data.login_body_type,
            "token_json_path": data.token_json_path,
            "expires_in_json_path": data.expires_in_json_path,
            "expires_at_json_path": data.expires_at_json_path,
            "authorization_header": data.authorization_header,
            "authorization_scheme": data.authorization_scheme,
            "refresh_skew_seconds": data.refresh_skew_seconds,
        }

    @staticmethod
    def _public_response(entity: MonitorAuthentication) -> MonitorAuthenticationResponse:
        return MonitorAuthenticationResponse(
            id=entity.id,
            monitor_id=entity.monitor_id,
            auth_type=entity.auth_type,
            configured=bool(entity.encrypted_credentials),
            login_url=entity.login_url,
            login_method=entity.login_method,
            login_body_type=entity.login_body_type,
            token_json_path=entity.token_json_path,
            expires_in_json_path=entity.expires_in_json_path,
            expires_at_json_path=entity.expires_at_json_path,
            authorization_header=entity.authorization_header,
            authorization_scheme=entity.authorization_scheme,
            refresh_skew_seconds=entity.refresh_skew_seconds,
        )


def get_monitor_authentication_service(
    session: AsyncSession = Depends(get_db),
) -> MonitorAuthenticationService:
    return MonitorAuthenticationService(session)
