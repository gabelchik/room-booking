import uuid

from src.db.models import Booking, Slot
from .base import BaseRepository

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from datetime import datetime

class BookingRepository(BaseRepository[Booking]):
    def __init__(self, session: AsyncSession):
        super().__init__(Booking, session)

    async def has_active_booking(self, slot_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Booking).where(and_(Booking.slot_id == slot_id, Booking.status == "active"))
        )
        return result.scalar_one_or_none() is not None

    async def get_user_future_bookings(self, user_id: uuid.UUID, now: datetime) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .join(Booking.slot)
            .where(Booking.user_id == user_id, Slot.start >= now)
            .order_by(Slot.start)
        )
        return result.scalars().all()

    async def get_all_paginated(self, page: int, page_size: int) -> tuple[list[Booking], int]:
        offset = (page - 1) * page_size
        total = await self.session.scalar(select(func.count()).select_from(Booking))
        result = await self.session.execute(
            select(Booking)
            .order_by(Booking.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        bookings = result.scalars().all()
        return bookings, total