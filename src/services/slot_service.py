import uuid

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.db.repositories.slot_repository import SlotRepository
from src.db.repositories.room_repository import RoomRepository
from src.core.exceptions import NotFoundError

class SlotService:
    def __init__(self, slot_repo: SlotRepository, room_repo: RoomRepository):
        self.slot_repo = slot_repo
        self.room_repo = room_repo

    async def get_available_slots_for_date(self, room_id: uuid.UUID, target_date: date):
        room = await self.room_repo.get(room_id)
        if not room:
            raise NotFoundError(code="ROOM_NOT_FOUND", message="Room not found")

        start_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=ZoneInfo("UTC"))
        end_day = start_day + timedelta(days=1)

        slots = await self.slot_repo.get_available_slots_for_date(room_id, start_day, end_day)

        return slots