from datetime import UTC, datetime, timedelta
import logging
from uuid import UUID

from fastapi import Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.security import get_password_hash, verify_password
from app.db.database import get_db
from app.schemas import PaginatedResponse

from ...dependencies.exception_utils import ensure_400, ensure_or_400, ensure_or_404
from ..user.user_session_service import UserSessionService
from .user_model import User
from .user_schema import (
    CreateUser,
    UpdateCurrentUser,
    UpdateUser,
    UserResponse,
    UserSearchRequest,
)
from .user_session_model import UserSession

logger = logging.getLogger("user-service")


class UserService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_session_service = UserSessionService(self._session)

    async def _validate_user_data(
        self,
        email: str | None = None,
        phone: str | None = None,
        id_: UUID | None = None,
    ) -> None:
        fields = (
            (User.phone, phone, "Phone already exists"),
            (User.email, email, "Email already exists"),
        )

        for column, value, message in fields:
            if value is None:
                continue

            conditions = [
                User.deleted_at.is_(None),
                column == value,
            ]

            if id_ is not None:
                conditions.append(User.id != id_)

            exists = await self._session.scalar(select(User.id).where(*conditions))

            if exists:
                raise HTTPException(
                    status_code=400,
                    detail=message,
                )

    async def _validate_user_update_data(
        self,
        data: User,
    ) -> None:
        conditions = []

        if data.email:
            conditions.append(
                User.email == data.email,
            )

        if not conditions:
            return

        duplicate = await self._session.scalar(
            select(User.id).where(
                User.deleted_at.is_(None),
                User.id != data.id,
                or_(*conditions),
            )
        )

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="User already exists",
            )

    async def _validate_single_session(
        self,
        user_id: UUID,
    ) -> None:
        user = await self._session.scalar(
            select(User).where(
                User.id == user_id,
            )
        )

        if not user or not user.single_session:
            return

        await self._session.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user.id,
                UserSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=datetime.now(UTC),
            )
        )

        await self._session.commit()

    async def create(
        self,
        data: CreateUser,
        current_user_id: UUID,
    ) -> User:
        await self._validate_user_data(
            email=str(data.email),
            phone=data.phone,
        )

        entity = User(
            created_by=current_user_id,
            name=data.name,
            email=str(data.email).strip(),
            password=await get_password_hash(
                data.password.strip(),
            ),
            phone=data.phone,
            single_session=data.single_session,
            mfa_enabled=data.mfa_enabled,
        )

        self._session.add(entity)

        await self._session.commit()

        return await self.get_by_id(entity.id)

    async def search(
        self,
        filters: UserSearchRequest,
    ) -> PaginatedResponse[UserResponse]:
        query = (
            select(User)
            .options(
                selectinload(User.who_created).load_only(
                    User.id,
                    User.name,
                ),
                selectinload(User.who_updated).load_only(
                    User.id,
                    User.name,
                ),
            )
            .where(
                User.deleted_at.is_(None),
            )
        )

        if filters.keyword:
            like = f"%{filters.keyword.strip()}%"

            query = query.where(
                or_(
                    User.name.ilike(like),
                    User.email.ilike(like),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())

        total = await self._session.scalar(count_query) or 0

        query = (
            query.order_by(User.name.asc())
            .offset((filters.page - 1) * filters.size)
            .limit(filters.size)
        )

        result = await self._session.execute(query)

        items = result.scalars().all()

        return PaginatedResponse.create(
            total=total,
            page=filters.page,
            size=filters.size,
            items=[
                UserResponse.model_validate(
                    item,
                    from_attributes=True,
                )
                for item in items
            ],
        )

    async def get_by_id(
        self,
        id_: UUID,
    ) -> User:
        user = await self._session.scalar(
            select(User)
            .options(
                joinedload(User.who_created).load_only(
                    User.name,
                ),
                joinedload(User.who_updated).load_only(
                    User.name,
                ),
            )
            .where(
                User.id == id_,
                User.deleted_at.is_(None),
            )
            .execution_options(
                populate_existing=True,
            )
        )

        return ensure_or_404(
            user,
            "User not found",
        )

    async def get_by_email(
        self,
        email: EmailStr,
    ) -> User:
        user = await self._session.scalar(
            select(User)
            .options(
                joinedload(User.who_created).load_only(
                    User.name,
                ),
                joinedload(User.who_updated).load_only(
                    User.name,
                ),
            )
            .where(
                User.email == str(email),
                User.deleted_at.is_(None),
            )
            .execution_options(
                populate_existing=True,
            )
        )

        return ensure_or_404(
            user,
            "User not found",
        )

    async def get_by_password_reset_token(
        self,
        token: str,
    ) -> User:
        user = await self._session.scalar(
            select(User).where(
                User.password_recovery == token,
                User.password_recovery_expire >= datetime.now(UTC),
            )
        )

        return ensure_or_404(
            user,
            "Not a valid token or expired",
        )

    async def verify_by_password(
        self,
        password: str,
        id_: UUID,
    ) -> bool:
        user = await self.get_by_id(id_)

        ensure_400(
            user is None,
            "Incorrect email or password.",
        )

        ensure_or_400(
            await verify_password(
                password,
                user.password,
            ),
            "Invalid credentials.",
        )

        return True

    async def update(
        self,
        id_: UUID,
        data: UpdateUser,
        current_user_id: UUID,
    ) -> User:
        entity = await self.get_by_id(id_)

        await self._validate_user_data(
            email=str(data.email) if data.email else None,
            phone=data.phone,
            id_=id_,
        )

        if data.mfa_enabled is False:
            entity.mfa_enabled = False
            entity.mfa_secret = None

        elif data.mfa_enabled:
            await self._user_session_service.revoke_user_sessions(
                entity.id,
            )

        try:
            data_dict = data.model_dump(
                exclude_unset=True,
            )

            for field, value in data_dict.items():
                setattr(entity, field, value)

            entity.updated_by = current_user_id

            await self._session.commit()

            return await self.get_by_id(entity.id)

        except Exception as error:
            await self._session.rollback()

            raise HTTPException(
                status_code=400,
                detail=f"Update failed - {error}",
            ) from error

    async def update_current_user(
        self,
        data: UpdateCurrentUser,
        current_user_id: UUID,
    ) -> User:
        return await self.update(
            id_=current_user_id,
            current_user_id=current_user_id,
            data=UpdateUser(
                name=data.name,
                email=data.email,
                phone=data.phone,
            ),
        )

    async def update_password(
        self,
        user: User,
        new_password: str,
    ) -> None:
        try:
            user.password = await get_password_hash(
                new_password,
            )

            user.password_recovery_expire = None

            await self._session.commit()

        except Exception as error:
            await self._session.rollback()

            ensure_400(
                True,
                f"Password update failed: {error}",
            )

    async def update_user_password_reset_token(
        self,
        email: EmailStr,
        token: str,
    ) -> None:
        entity = await self.get_by_email(email)

        entity.password_recovery = token

        entity.password_recovery_expire = (datetime.now(UTC) + timedelta(hours=1)).replace(
            tzinfo=None
        )

        await self._session.commit()

    async def delete(
        self,
        id_: UUID,
        current_user_id: UUID,
    ) -> None:
        entity = await self.get_by_id(id_)

        if entity.deleted_at is not None:
            raise HTTPException(
                status_code=404,
                detail="Not found",
            )

        entity.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        entity.updated_by = current_user_id

        await self._session.commit()


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session)
