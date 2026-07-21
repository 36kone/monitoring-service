from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.modules.user import User

ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin123"


async def seed_db(db: AsyncSession) -> None:
    db.add(
        User(
            id=uuid4(),
            name="Admin Test",
            email=ADMIN_EMAIL,
            password=await get_password_hash(ADMIN_PASSWORD),
            phone="5511111111111",
            is_admin=True,
            is_super_user=True,
        )
    )
    await db.commit()
