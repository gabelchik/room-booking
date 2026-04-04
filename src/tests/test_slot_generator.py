from uuid import uuid4

from datetime import date, time, timedelta
from zoneinfo import ZoneInfo

from src.services.slot_generator import generate_slots_for_schedule
from src.db.models import Schedule


def test_generate_slots_for_schedule():
    schedule = Schedule(
        id=uuid4(),
        room_id=uuid4(),
        days_of_week=[1, 3, 5],
        start_time=time(9, 0),
        end_time=time(10, 0)
    )
    start_date = date(2026, 4, 6)
    end_date = date(2026, 4, 12)
    slots = generate_slots_for_schedule(schedule, start_date, end_date)

    assert len(slots) == 6
    for slot in slots:
        assert slot.end - slot.start == timedelta(minutes=30)
        assert slot.room_id == schedule.room_id
        assert slot.start.tzinfo == ZoneInfo("UTC")
        assert slot.end.tzinfo == ZoneInfo("UTC")


def test_generate_slots_no_days():
    schedule = Schedule(
        id=uuid4(),
        room_id=uuid4(),
        days_of_week=[],
        start_time=time(9, 0),
        end_time=time(10, 0)
    )
    start_date = date(2026, 4, 6)
    end_date = date(2026, 4, 12)
    slots = generate_slots_for_schedule(schedule, start_date, end_date)
    assert len(slots) == 0


def test_generate_slots_start_time_equal_end():
    schedule = Schedule(
        id=uuid4(),
        room_id=uuid4(),
        days_of_week=[1],
        start_time=time(10, 0),
        end_time=time(10, 0)
    )
    start_date = date(2026, 4, 6)
    end_date = date(2026, 4, 12)
    slots = generate_slots_for_schedule(schedule, start_date, end_date)
    assert len(slots) == 0


def test_generate_slots_end_time_before_start_date():
    schedule = Schedule(
        id=uuid4(),
        room_id=uuid4(),
        days_of_week=[1],
        start_time=time(10, 0),
        end_time=time(9, 0)
    )
    start_date = date(2026, 4, 6)
    end_date = date(2026, 4, 12)
    slots = generate_slots_for_schedule(schedule, start_date, end_date)
    assert len(slots) == 0
