from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.database import get_db
from app.modules.user import User, UserSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/core/v1/auth/login")
bearer_scheme = HTTPBearer(auto_error=False)


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_mfa_user(
    bearer: HTTPAuthorizationCredentials = Security(bearer_scheme),
    oauth2: str | None = Depends(oauth2_scheme),
) -> User:
    token = bearer.credentials if bearer else oauth2
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("token_role") != "mfa":
        raise credentials_exception

    try:
        user_id = UUID(payload.get("sub"))
    except Exception as e:
        raise credentials_exception from e

    async with get_db() as db:
        user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise credentials_exception

    return user


async def get_auth_user(
    bearer: HTTPAuthorizationCredentials = Security(bearer_scheme),
    oauth2: str | None = Depends(oauth2_scheme),
) -> User:
    token = bearer.credentials if bearer else oauth2
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("token_role") == "mfa":
        raise credentials_exception

    try:
        user_id = UUID(payload.get("sub"))
        session_id = UUID(payload.get("sid"))
    except Exception as e:
        raise credentials_exception from e

    query = (
        select(User, UserSession)
        .join(UserSession, UserSession.user_id == User.id)
        .where(User.id == user_id, UserSession.id == session_id)
    )

    async with get_db() as db:
        result = await db.execute(query)

    result = result.first()

    if not result:
        raise credentials_exception

    user, user_session = result

    now_utc = datetime.now(UTC)

    expire_at = user_session.expire_at
    if expire_at.tzinfo is None:
        expire_at = expire_at.replace(tzinfo=UTC)

    revoked_at = user_session.revoked_at
    if revoked_at is not None and revoked_at.tzinfo is None:
        revoked_at = revoked_at.replace(tzinfo=UTC)

    if revoked_at is not None or expire_at < now_utc:
        raise credentials_exception

    return user


async def auth_guard(
    request: Request,
    user: User = Depends(get_auth_user),
) -> None:
    endpoint = request.scope.get("endpoint")

    if endpoint is None:
        return

    if user.is_admin or user.is_super_user:
        return
