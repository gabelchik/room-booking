import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User

async def ensure_default_users(session: AsyncSession, admin_uuid: uuid.UUID, user_uuid: uuid.UUID):
    admin = await session.get(User, admin_uuid)
    if not admin:
        session.add(User(id=admin_uuid, role="admin"))

    user = await session.get(User, user_uuid)
    if not user:
        session.add(User(id=user_uuid, role="user"))
    await session.commit()
