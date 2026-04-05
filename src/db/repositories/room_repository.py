from .base import BaseRepository
from src.db.models import Room

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class RoomRepository(BaseRepository[Room]):
    def __init__(self, session: AsyncSession):
        super().__init__(Room, session)

    async def get_all_ordered(self) -> list[Room]:
        result = await self.session.execute(select(Room).order_by(Room.created_at))
        return result.scalars().all()