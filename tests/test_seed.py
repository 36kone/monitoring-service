"""Valida o seed base (usuário admin/super_user)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.modules.user import User
from tests.seed import ADMIN_EMAIL, ADMIN_PASSWORD


@pytest.mark.asyncio
async def test_admin_user_is_seeded(db_session: AsyncSession) -> None:
    user = await db_session.scalar(select(User).where(User.email == ADMIN_EMAIL))

    assert user is not None
    assert user.is_admin is True
    assert user.is_super_user is True
    assert await verify_password(ADMIN_PASSWORD, user.password)
