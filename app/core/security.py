from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Query
from fastapi.concurrency import run_in_threadpool
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel

from app.core.config import settings


class CreateToken(BaseModel):
    sub: str
    token_role: str
    sid: str | None = None


password_hash = PasswordHash.recommended()


async def get_password_hash(password: str) -> str:
    return await run_in_threadpool(password_hash.hash, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(password_hash.verify, plain_password, hashed_password)


def create_access_token(data: CreateToken, expires_delta: timedelta | None = None) -> str:
    to_encode: dict[str, object] = {
        "sub": data.sub,
        "token_role": data.token_role,
    }
    if data.sid is not None:
        to_encode["sid"] = data.sid
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except InvalidTokenError:
        return None


def get_first_access_payload(token: str = Query(...)) -> dict:
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "first_access":
        raise HTTPException(status_code=403, detail="Access denied")
    return payload
