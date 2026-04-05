import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.room_service import get_all_rooms, create_room_s
from src.schemas.room import RoomCreate


@pytest.mark.asyncio
async def test_get_all_rooms():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = mock_result

    rooms = await get_all_rooms(mock_session)

    assert len(rooms) == 2
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_room():
    mock_session = AsyncMock()
    room_data = RoomCreate(name="Test", description="Desc", capacity=5)
    room = await create_room_s(mock_session, room_data)

    assert room.name == "Test"
    assert room.description == "Desc"
    assert room.capacity == 5

    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
