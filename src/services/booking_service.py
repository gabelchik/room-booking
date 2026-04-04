import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.models import Slot, Booking


async def get_booking_by_id(session: AsyncSession, booking_id: uuid.UUID) -> Booking | None:
    return await session.get(Booking, booking_id)


async def has_active_booking(session: AsyncSession, slot_id: uuid.UUID) -> bool:
    query = select(Booking).where(Booking.slot_id == slot_id, Booking.status == "active")
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_booking_s(session: AsyncSession, slot_id: uuid.UUID, user_id: uuid.UUID) -> Booking:
    new_booking = Booking(slot_id=slot_id,
                          user_id=user_id,
                          status="active")

    session.add(new_booking)

    await session.flush()
    await session.refresh(new_booking)

    return new_booking


async def cancel_booking_s(session: AsyncSession, booking: Booking) -> Booking:
    booking.status = "cancelled"

    await session.flush()
    await session.refresh(booking)

    return booking


async def get_user_future_bookings(session: AsyncSession, user_id: uuid.UUID) -> list[Booking]:
    now = datetime.now(ZoneInfo("UTC"))

    query = (
        select(Booking)
        .join(Booking.slot)
        .where(Booking.user_id == user_id, Slot.start >= now)
        .order_by(Slot.start)
    )
    result = await session.execute(query)

    return result.scalars().all()


async def get_all_bookings_paginated(
    session: AsyncSession, page: int, page_size: int
) -> tuple[list[Booking], int]:
    offset = (page - 1) * page_size

    query = select(func.count()).select_from(Booking)
    total = await session.scalar(query)

    stmt = select(Booking).order_by(Booking.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(stmt)
    bookings = result.scalars().all()

    return bookings, total