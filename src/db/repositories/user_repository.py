from .base import BaseRepository
from src.db.models import User

from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_role(self, role: str) -> list[User]:
        from sqlalchemy import select
        result = await self.session.execute(select(User).where(User.role == role))
        return result.scalars().all()