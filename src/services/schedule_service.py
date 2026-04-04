import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from src.db.models import Room, Schedule
from src.services.slot_generator import generate_slots_for_schedule


async def get_room_by_id(session: AsyncSession, room_id: uuid.UUID) -> Room | None:
    return await session.get(Room, room_id)


async def get_existing_schedule(session: AsyncSession, room_id: uuid.UUID) -> Schedule | None:
    query = select(Schedule).where(Schedule.room_id == room_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def create_schedule_and_slots(
    session: AsyncSession,
    room_id: uuid.UUID,
    days_of_week: list[int],
    start_time: time,
    end_time: time
) -> Schedule:
    new_schedule = Schedule(
        room_id=room_id,
        days_of_week=days_of_week,
        start_time=start_time,
        end_time=end_time
    )
    session.add(new_schedule)

    start_date = datetime.now(ZoneInfo("UTC")).date()
    end_date = start_date + timedelta(days=7)
    slots = generate_slots_for_schedule(new_schedule, start_date, end_date)
    session.add_all(slots)

    await session.commit()
    await session.refresh(new_schedule)

    return new_schedule
