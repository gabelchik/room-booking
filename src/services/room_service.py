from src.db.repositories.room_repository import RoomRepository
from src.schemas.room import RoomCreate
from src.db.models import Room


class RoomService:
    def __init__(self, repo: RoomRepository):
        self.repo = repo

    async def get_all_rooms(self):
        return await self.repo.get_all_ordered()

    async def create_room(self, room_data: RoomCreate):
        new_room = Room(
            name=room_data.name,
            description=room_data.description,
            capacity=room_data.capacity
        )
        return await self.repo.add(new_room)