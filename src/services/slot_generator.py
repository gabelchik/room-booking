from uuid import uuid4
import datetime as dt
from zoneinfo import ZoneInfo
from sqlalchemy import select, func
from src.db.models import Schedule, Slot
from src.db.session import new_session


def generate_slots_for_schedule(
        schedule: Schedule,
        start_date: dt.date,
        end_date: dt.date) ->list[Slot]:
    slots = []

    current_data = start_date
    while current_data <= end_date:
        if current_data.isoweekday() in schedule.days_of_week:
            start_dt = dt.datetime.combine(
                current_data, schedule.start_time).replace(tzinfo=ZoneInfo("UTC"))
            end_dt = dt.datetime.combine(
                current_data, schedule.end_time).replace(tzinfo=ZoneInfo("UTC"))

            slot_start = start_dt
            while slot_start + dt.timedelta(minutes=30) <= end_dt:
                slot_end = slot_start + dt.timedelta(minutes=30)
                slot = Slot(
                    id=uuid4(),
                    room_id=schedule.room_id,
                    start=slot_start,
                    end=slot_end
                )
                slots.append(slot)
                slot_start += dt.timedelta(minutes=30)

        current_data += dt.timedelta(days=1)

    return slots


async def generate_future_slots_for_schedules():
    async with new_session() as session:
        max_slot_subquery = (
            select(
                Slot.room_id,
                func.max(Slot.start).label("max_slot_date")
            )
            .group_by(Slot.room_id)
            .subquery()
        )

        query = (
            select(Schedule, max_slot_subquery.c.max_slot_date)
            .join(max_slot_subquery, Schedule.room_id == max_slot_subquery.c.room_id)
        )
        stmt = await session.execute(query)

        for schedule, max_slot_date in stmt:

            target_date = dt.datetime.now(ZoneInfo("UTC")).date() + dt.timedelta(days=7)
            if max_slot_date.date() < target_date:
                start_date = max_slot_date.date() + dt.timedelta(days=1)
                end_date = target_date
                new_slots = generate_slots_for_schedule(schedule, start_date, end_date)
                if new_slots:
                    session.add_all(new_slots)

        await session.commit()
