import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.db.models import Slot


async def get_slot_by_id(session: AsyncSession, slot_id: uuid.UUID) -> Slot | None:
    return await session.get(Slot, slot_id)


async def get_available_slots_for_date(
    session: AsyncSession,
    room_id: uuid.UUID,
    target_date: datetime.date
) -> list[Slot]:
    start_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=ZoneInfo("UTC"))
    end_day = start_day + timedelta(days=1)
    query = (
        select(Slot)
        .options(selectinload(Slot.booking))
        .where(
            Slot.room_id == room_id,
            Slot.start >= start_day,
            Slot.start < end_day)
        .order_by(Slot.start)
    )
    result = await session.execute(query)
    slots = result.scalars().all()

    available_slots = []
    for slot in slots:
        if not slot.booking or slot.booking.status != "active":
            available_slots.append(slot)

    return available_slots