import uuid

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.db.models import Schedule

from src.db.repositories.room_repository import RoomRepository
from src.db.repositories.schedule_repository import ScheduleRepository
from src.db.repositories.slot_repository import SlotRepository

from src.services.slot_generator import generate_slots_for_schedule
from src.core.exceptions import NotFoundError, ConflictError


class ScheduleService:
    def __init__(
        self,
        room_repo: RoomRepository,
        schedule_repo: ScheduleRepository,
        slot_repo: SlotRepository
    ):
        self.room_repo = room_repo
        self.schedule_repo = schedule_repo
        self.slot_repo = slot_repo


    async def get_room_by_id(self, room_id: uuid.UUID):
        return await self.room_repo.get(room_id)


    async def get_existing_schedule(self, room_id: uuid.UUID):
        return await self.schedule_repo.get_by_room_id(room_id)


    async def create_schedule_and_slots(
        self,
        room_id: uuid.UUID,
        days_of_week: list[int],
        start_time: time,
        end_time: time
    ) -> Schedule:
        room = await self.room_repo.get(room_id)
        if not room:
            raise NotFoundError(code="ROOM_NOT_FOUND", message="Room not found")

        existing = await self.schedule_repo.get_by_room_id(room_id)
        if existing:
            raise ConflictError(code="SCHEDULE_EXISTS", message="Schedule already exists for this room")

        new_schedule = Schedule(
            room_id=room_id,
            days_of_week=days_of_week,
            start_time=start_time,
            end_time=end_time
        )
        new_schedule = await self.schedule_repo.add(new_schedule)

        start_date = datetime.now(ZoneInfo("UTC")).date()
        end_date = start_date + timedelta(days=7)
        slots = generate_slots_for_schedule(new_schedule, start_date, end_date)

        if slots:
            await self.slot_repo.add_all(slots)

        return new_schedule