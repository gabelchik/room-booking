import uuid
from .base import BaseRepository

from src.db.models import User
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.get(user_id)

    async def create_user(self, user_id: uuid.UUID, role: str) -> User:
        user = User(id=user_id, role=role)
        return await self.add(user)