from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models import Room
from src.schemas.room import RoomCreate


async def get_all_rooms(session: AsyncSession) -> list[Room]:
    query = select(Room).order_by(Room.created_at)
    result = await session.execute(query)
    return result.scalars().all()


async def create_room_s(session: AsyncSession, room_data: RoomCreate) -> Room:
    new_room = Room(
        name=room_data.name,
        description=room_data.description,
        capacity=room_data.capacity
    )
    session.add(new_room)
    await session.flush()
    await session.refresh(new_room)
    return new_room