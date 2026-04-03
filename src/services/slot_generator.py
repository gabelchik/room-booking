from uuid import uuid4
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from src.db.models import Schedule, Slot


def generate_slot_for_schedule(
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
