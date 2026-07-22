from datetime import UTC, datetime, timedelta
import uuid
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.dependencies.exception_utils import ensure_or_404
from app.schemas import PaginatedResponse

from .user_model import User
from .user_session_model import UserSession
from .user_session_schema import (
    UpdateUserSession,
    UserSessionResponse,
    UserSessionSearchRequest,
)


class UserSessionService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_user_session(
        self,
        user: User,
        ipv4: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        if user.single_session:
            await self.revoke_user_sessions(user.id)

        user_session = UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            expire_at=(
                datetime.now(UTC) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE)
            ).replace(tzinfo=None),
            user_agent=user_agent,
            ipv4=ipv4,
        )

        self._session.add(user_session)

        await self._session.commit()
        await self._session.refresh(user_session)

        return user_session

    async def get_by_id(self, id_: UUID) -> UserSession:
        user_session = await self._session.scalar(
            select(UserSession).where(
                UserSession.id == id_,
            )
        )

        return ensure_or_404(
            user_session,
            "User session not found",
        )

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> UserSession | None:
        return await self._session.scalar(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .order_by(UserSession.created_at.desc())
        )

    async def search(
        self,
        filters: UserSessionSearchRequest,
    ) -> PaginatedResponse[UserSessionResponse]:
        query = (
            select(UserSession)
            .join(UserSession.user)
            .options(
                selectinload(UserSession.user).load_only(User.name),
                selectinload(UserSession.who_revoked).load_only(User.name),
            )
        )

        if filters.keyword:
            like = f"%{filters.keyword.strip()}%"

            query = query.where(
                or_(
                    User.name.ilike(like),
                )
            )

        if filters.user_id:
            query = query.where(
                UserSession.user_id == filters.user_id,
            )

        if filters.revoked_by:
            query = query.where(
                UserSession.revoked_by == filters.revoked_by,
            )

        if filters.is_revoked is not None:
            if filters.is_revoked:
                query = query.where(
                    UserSession.revoked_at.is_not(None),
                )
            else:
                query = query.where(
                    UserSession.revoked_at.is_(None),
                )

        count_query = select(func.count()).select_from(query.subquery())

        total = await self._session.scalar(count_query) or 0

        query = query.offset((filters.page - 1) * filters.size).limit(filters.size)

        result = await self._session.execute(query)

        items = result.scalars().all()

        return PaginatedResponse.create(
            total=total,
            page=filters.page,
            size=filters.size,
            items=[
                UserSessionResponse.model_validate(
                    item,
                    from_attributes=True,
                )
                for item in items
            ],
        )

    async def update(
        self,
        data: UpdateUserSession,
    ) -> UserSession:
        entity = await self.get_by_id(data.id)

        try:
            data_dict = data.model_dump(
                exclude_unset=True,
            )

            for field, value in data_dict.items():
                setattr(entity, field, value)

            await self._session.commit()
            await self._session.refresh(entity)

            return entity

        except HTTPException as error:
            await self._session.rollback()

            raise HTTPException(
                status_code=400,
                detail=f"Update failed - {error}",
            ) from error

    async def revoke_session(
        self,
        id_: UUID,
        current_user_id: UUID | None = None,
    ) -> None:
        await self._session.execute(
            update(UserSession)
            .where(
                and_(
                    UserSession.id == id_,
                    UserSession.revoked_at.is_(None),
                )
            )
            .values(
                revoked_at=datetime.now(UTC).replace(tzinfo=None),
                revoked_by=current_user_id,
            )
        )

        await self._session.commit()

    async def revoke_user_sessions(
        self,
        user_id: UUID,
    ) -> None:
        await self._session.execute(
            update(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                )
            )
            .values(
                revoked_at=datetime.now(UTC).replace(tzinfo=None),
            )
        )

        await self._session.commit()
