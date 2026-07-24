from datetime import UTC, datetime, timedelta
import secrets
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    CreateToken,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.db.database import get_db
from app.dependencies.email_sender import EmailSender
from app.dependencies.exception_utils import ensure_or_400
from app.modules.auth.auth_schema import (
    ChangePasswordRequest,
    Enable2FARequest,
    Message,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
)
from app.modules.user import SimpleUserResponse, User, UserService, UserSessionService
from app.modules.user.user_session_model import UserSession


class AuthService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_session_service = UserSessionService(session)
        self._user_service = UserService(session)
        self._email_sender = EmailSender()

    async def _create_user_access_token(
        self, user: User, ipv4: str | None, user_agent: str | None
    ) -> Token:
        user_session = await self._user_session_service.create_user_session(
            user, ipv4=ipv4, user_agent=user_agent
        )
        return self._create_token_response(user, user_session.id)

    def _create_token_response(self, user: User, session_id: UUID) -> Token:
        access_token = create_access_token(
            CreateToken(
                sub=str(user.id),
                token_role="user",
                sid=str(session_id),
            )
        )
        refresh_token = create_access_token(
            CreateToken(
                sub=str(user.id),
                token_role="refresh",
                sid=str(session_id),
            ),
            expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE),
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=SimpleUserResponse.model_validate(user),
            token_role="user",
        )

    async def refresh_token(self, token: str) -> Token:
        payload = decode_access_token(token)

        if not payload or payload.get("token_role") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        try:
            user_id = UUID(payload["sub"])
            session_id = UUID(payload["sid"])
        except (KeyError, ValueError, TypeError) as error:
            raise HTTPException(status_code=401, detail="Invalid refresh token") from error

        result = await self._session.execute(
            select(User, UserSession)
            .join(UserSession, UserSession.user_id == User.id)
            .where(
                User.id == user_id,
                UserSession.id == session_id,
                User.deleted_at.is_(None),
                User.is_active.is_(True),
                UserSession.revoked_at.is_(None),
            )
        )
        row = result.first()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user, user_session = row
        expire_at = user_session.expire_at

        if expire_at.tzinfo is None:
            expire_at = expire_at.replace(tzinfo=UTC)

        if expire_at < datetime.now(UTC):
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return self._create_token_response(user, user_session.id)

    async def login(self, request: Request, form_data: OAuth2PasswordRequestForm) -> Token | dict:
        identifier = form_data.username.strip()
        user = await self._session.scalar(
            select(User).where(
                User.email == identifier,
                User.deleted_at.is_(None),
                User.is_active.is_(True),
            )
        )

        if not user:
            raise HTTPException(400, "Invalid credentials.")

        ensure_or_400(
            await verify_password(form_data.password.strip(), user.password),
            "Invalid credentials.",
        )

        if user.mfa_enabled:
            temp_token = create_access_token(
                CreateToken(sub=str(user.id), token_role="mfa"),
                expires_delta=timedelta(minutes=5),
            )

            if user.mfa_secret is None:
                otp_secret, uri = await self.setup_2fa(user.id)
                return {
                    "access_token": temp_token,
                    "otp_secret": otp_secret,
                    "otpauth_url": uri,
                }

            return Token(
                access_token=temp_token,
                token_type="bearer",
                user=SimpleUserResponse.model_validate(user),
                token_role="mfa",
            )

        ipv4 = request.client.host if request.client else None

        return await self._create_user_access_token(
            user,
            ipv4=ipv4,
            user_agent=request.headers.get("user-agent"),
        )

    async def change_password(self, data: ChangePasswordRequest, user_id: UUID) -> Message:
        current_user = await self._user_service.get_by_id(user_id)
        ensure_or_400(
            await verify_password(data.current_password, current_user.password),
            "Current password is incorrect",
        )

        current_user.password = await get_password_hash(data.new_password)

        await self._session.commit()
        await self._session.refresh(current_user)

        return Message(message="Password changed successfully")

    async def request_password_reset(self, data: PasswordResetRequest) -> Message:
        user = await self._user_service.get_by_email(data.email)
        reset_token = secrets.token_urlsafe(32)

        await self._user_service.update_user_password_reset_token(
            email=data.email,
            token=reset_token,
        )

        reset_url = f"{settings.API_PREFIX}/auth/reset-password?token={reset_token}"

        await self._email_sender.send_email(
            subject="Recuperação de Senha",
            email_to=data.email,
            template_path="app/templates/password_reset.html",
            context={"username": user.name, "reset_url": reset_url},
        )

        return Message(message="Email for reset password sent successfully")

    async def confirm_password_reset(self, data: PasswordResetConfirm) -> Message:
        user = await self._user_service.get_by_password_reset_token(data.token)
        await self._user_service.update_password(user, data.new_password)
        return Message(message="Senha redefinida com sucesso")

    async def verify_2fa(self, code: str, request: Request, token: str) -> Token:
        payload = decode_access_token(token)

        if not payload or payload.get("token_role") != "mfa":
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_id = payload.get("sub")
        user = await self._user_service.get_by_id(UUID(user_id))

        if not user.mfa_secret:
            raise HTTPException(status_code=400, detail="Missing MFA setup")

        ensure_or_400(pyotp.TOTP(user.mfa_secret).verify(code), "Invalid code")

        return await self._create_user_access_token(
            user,
            ipv4=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    async def setup_2fa(self, user_id: UUID) -> tuple[str, str]:
        current_user = await self._user_service.get_by_id(user_id)
        secret = pyotp.random_base32()
        current_user.mfa_secret = secret

        await self._session.commit()

        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=current_user.email,
            issuer_name="Monitoring",
        )

        return secret, uri

    async def enable_2fa(self, payload: Enable2FARequest, user_id: UUID) -> Message:
        current_user = await self._user_service.get_by_id(user_id)

        if not current_user.mfa_secret:
            raise HTTPException(status_code=400, detail="Missing MFA setup")

        ensure_or_400(pyotp.TOTP(current_user.mfa_secret).verify(payload.code), "Invalid code")
        current_user.mfa_enabled = True

        await self._session.commit()

        return Message(message="2FA activated")

    async def disable_2fa(self, user_id: UUID) -> Message:
        current_user = await self._user_service.get_by_id(user_id)
        ensure_or_400(current_user.mfa_enabled, "2FA already disabled")

        current_user.mfa_enabled = False
        current_user.mfa_secret = None

        await self._session.commit()
        await self._session.refresh(current_user)

        return Message(message="2fa disabled")


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)
