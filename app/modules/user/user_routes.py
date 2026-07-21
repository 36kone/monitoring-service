import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.db.database import get_db
from app.dependencies.authentication import auth_guard
from app.dependencies.current_user import CurrentUser
from app.dependencies.rate_limit import rate_limited
from app.modules.user import CreateUser, UserResponse, UserSearchRequest, UserService
from app.modules.user.user_schema import UpdateUser
from app.schemas import (
    PaginatedResponse,
)

user_router = APIRouter(
    dependencies=[Depends(auth_guard)],
    route_class=rate_limited("100/minute"),
)

logger = logging.getLogger("users")


@user_router.post("/", status_code=201, response_model=UserResponse)
async def create_user(data: CreateUser, current_user: CurrentUser):
    try:
        async with get_db() as db:
            return await UserService(db).create(
                data,
                current_user.id,
            )

    except Exception as e:
        logger.exception(f"[CREATE_USER] -> {e}")
        raise


@user_router.get("/", status_code=200, response_model=PaginatedResponse[UserResponse])
async def search_user_endpoint(
    filters: Annotated[
        UserSearchRequest,
        Query(),
    ],
):
    try:
        async with get_db() as db:
            return await UserService(db).search(filters)

    except Exception as e:
        logger.exception(f"[SEARCH_USERS] -> {e}")
        raise


@user_router.get("/{id_}", status_code=200, response_model=UserResponse)
async def get_user_by_id(id_: UUID):
    try:
        async with get_db() as db:
            return await UserService(db).get_by_id(id_)

    except Exception as e:
        logger.exception(f"[GET_USER_BY_ID] -> {e}")
        raise


@user_router.put("/{id_}", status_code=200, response_model=UserResponse)
async def update_user(id_: UUID, data: UpdateUser, current_user: CurrentUser):
    try:
        async with get_db() as db:
            return await UserService(db).update(
                id_,
                data,
                current_user.id,
            )

    except Exception as e:
        logger.exception(f"[UPDATE_USER] -> {e}")
        raise


@user_router.delete("/{id_}", status_code=204)
async def delete_user(id_: UUID, current_user: CurrentUser):
    try:
        async with get_db() as db:
            await UserService(db).delete(
                id_,
                current_user.id,
            )

    except Exception as e:
        logger.exception(
            f"[DELETE_USER] -> {e}",
        )
        raise
