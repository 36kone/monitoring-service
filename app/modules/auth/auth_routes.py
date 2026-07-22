import logging

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.db.database import get_db
from app.dependencies.authentication import get_mfa_user, oauth2_scheme
from app.dependencies.current_user import CurrentUser
from app.dependencies.rate_limit import rate_limited
from app.modules.auth.auth_schema import (
    ChangePasswordRequest,
    Enable2FARequest,
    Message,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    Token,
    VerifyUserByPassword,
)
from app.modules.auth.auth_service import AuthService
from app.modules.user import SimpleUserResponse, UpdateCurrentUser, User, UserResponse, UserService

auth_router = APIRouter(route_class=rate_limited(default_limit="100/minute"))
logger = logging.getLogger("auth")


@auth_router.post("/login", response_model=Token | dict)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    async with get_db() as db:
        return await AuthService(db).login(request, form_data)


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshTokenRequest):
    async with get_db() as db:
        return await AuthService(db).refresh_token(data.refresh_token)


@auth_router.post("/verify-by-password")
async def verify_user_by_password(data: VerifyUserByPassword, current_user: CurrentUser):
    async with get_db() as db:
        return await UserService(db).verify_by_password(data.password, current_user.id)


@auth_router.get("/me", response_model=SimpleUserResponse)
async def read_current_user(current_user: CurrentUser):
    return current_user


@auth_router.put("/me", response_model=UserResponse)
async def update_authenticated_user(data: UpdateCurrentUser, current_user: CurrentUser):
    async with get_db() as db:
        return await UserService(db).update_current_user(data, current_user.id)


@auth_router.post("/forgot-password", response_model=Message)
async def request_password_reset(data: PasswordResetRequest):
    async with get_db() as db:
        return await AuthService(db).request_password_reset(data)


@auth_router.put("/change-password", response_model=Message)
async def change_password(data: ChangePasswordRequest, current_user: CurrentUser):
    async with get_db() as db:
        return await AuthService(db).change_password(data, current_user.id)


@auth_router.post("/reset-password", response_model=Message)
async def confirm_password_reset(data: PasswordResetConfirm):
    async with get_db() as db:
        return await AuthService(db).confirm_password_reset(data)


@auth_router.post("/verify-2fa/{code}", response_model=Token)
async def verify_2fa(code: str, request: Request, token: str = Depends(oauth2_scheme)):
    async with get_db() as db:
        return await AuthService(db).verify_2fa(code, request, token)


@auth_router.post("/setup-2fa")
async def setup_2fa(current_user: User = Depends(get_mfa_user)):
    async with get_db() as db:
        secret, uri = await AuthService(db).setup_2fa(current_user.id)
        return {"otp_secret": secret, "otpauth_url": uri}


@auth_router.post("/me/setup-2fa")
async def setup_2fa_for_authenticated_user(current_user: CurrentUser):
    async with get_db() as db:
        secret, uri = await AuthService(db).setup_2fa(current_user.id)
        return {"otp_secret": secret, "otpauth_url": uri}


@auth_router.post("/enable-2fa", response_model=Message)
async def enable_2fa(payload: Enable2FARequest, current_user: CurrentUser):
    async with get_db() as db:
        return await AuthService(db).enable_2fa(payload, current_user.id)


@auth_router.post("/disable-2fa", response_model=Message)
async def disable_2fa(current_user: CurrentUser):
    async with get_db() as db:
        return await AuthService(db).disable_2fa(current_user.id)
