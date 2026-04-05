import uuid

from .base import BaseRepository
from src.db.models import Slot

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime


class SlotRepository(BaseRepository[Slot]):
    def __init__(self, session: AsyncSession):
        super().__init__(Slot, session)

    async def add_all(self, slots: list[Slot]) -> None:
        self.session.add_all(slots)
        await self.session.flush()

    async def get_available_slots_for_date(
            self, room_id: uuid.UUID, start_day: datetime, end_day: datetime
    ) -> list[Slot]:
        result = await self.session.execute(
            select(Slot)
            .options(selectinload(Slot.booking))
            .where(
                Slot.room_id == room_id,
                Slot.start >= start_day,
                Slot.start < end_day
            )
            .order_by(Slot.start)
        )
        slots = result.scalars().all()

        available_slots = []

        for slot in slots:
            if not slot.booking or slot.booking.status != "active":
                available_slots.append(slot)

        return available_slots