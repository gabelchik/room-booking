import pytest
from unittest.mock import AsyncMock

from src.services.room_service import RoomService
from src.schemas.room import RoomCreate
from src.db.models import Room


@pytest.mark.asyncio
async def test_get_all_rooms():
    mock_repo = AsyncMock()
    mock_repo.get_all_ordered.return_value = [Room(), Room()]

    service = RoomService(mock_repo)
    rooms = await service.get_all_rooms()

    assert len(rooms) == 2
    mock_repo.get_all_ordered.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_room():
    mock_repo = AsyncMock()
    mock_repo.add.return_value = Room(name="Test", description="nothing", capacity=5)

    service = RoomService(mock_repo)

    room_data = RoomCreate(name="Test", description="nothing", capacity=5)
    room = await service.create_room(room_data)

    assert room.name == "Test"
    mock_repo.add.assert_awaited_once()