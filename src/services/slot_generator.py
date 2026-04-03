from uuid import uuid4
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, func
from src.db.models import Schedule, Slot
from src.db.session import new_session

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def generate_slots_for_schedule(
        schedule: Schedule,
        start_date: date,
        end_date: date) ->list[Slot]:
    slots = []

    current_data = start_date
    while current_data <= end_date:
        if current_data.isoweekday() in schedule.days_of_week:
            start_dt = datetime.combine(
                current_data, schedule.start_time).replace(tzinfo=ZoneInfo("UTC"))
            end_dt = datetime.combine(
                current_data, schedule.end_time).replace(tzinfo=ZoneInfo("UTC"))

            slot_start = start_dt
            while slot_start + timedelta(minutes=30) <= end_dt:
                slot_end = slot_start + timedelta(minutes=30)
                slot = Slot(
                    id=uuid4(),
                    room_id=schedule.room_id,
                    start=slot_start,
                    end=slot_end
                )
                slots.append(slot)
                slot_start += timedelta(minutes=30)

        current_data += timedelta(days=1)

    return slots


async def generate_future_slots_for_schedules():
    logger.info("Фоновая задача generate_missing_slots запущена")
    total_added = 0
    async with new_session() as session:
        query = await session.execute(select(Schedule))
        schedules = query.scalars().all()

        for schedule in schedules:
            stmt = await session.execute(
                select(func.max(Slot.start)).where(Slot.room_id == schedule.room_id)
            )
            max_date = stmt.scalar().date()

            target_date = date.today() + timedelta(days=7)
            if max_date < target_date:
                start_date = max_date + timedelta(days=1)
                end_date = target_date
                new_slots = generate_slots_for_schedule(schedule, start_date, end_date)
                if new_slots:
                    total_added += len(new_slots)
                    session.add_all(new_slots)
        logger.info(f"Фоновая задача завершена, добавлено {total_added}")
        await session.commit()