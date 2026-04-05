import uuid

from .base import BaseRepository
from src.db.models import Schedule

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class ScheduleRepository(BaseRepository[Schedule]):
    def __init__(self, session: AsyncSession):
        super().__init__(Schedule, session)

    async def get_by_room_id(self, room_id: uuid.UUID) -> Schedule | None:
        result = await self.session.execute(select(Schedule).where(Schedule.room_id == room_id))
        return result.scalar_one_or_none()