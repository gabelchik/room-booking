import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from uuid import uuid4
from datetime import time

from src.services.schedule_service import get_room_by_id, get_existing_schedule, create_schedule_and_slots
from src.db.models import Room, Schedule


@pytest.mark.asyncio
async def test_get_room_by_id_found():
    mock_session = AsyncMock()
    room_id = uuid4()
    expected_room = Room(id=room_id, name="Test")
    mock_session.get.return_value = expected_room

    room = await get_room_by_id(mock_session, room_id)

    assert room == expected_room
    mock_session.get.assert_awaited_once_with(Room, room_id)


@pytest.mark.asyncio
async def test_get_room_by_id_not_found():
    mock_session = AsyncMock()
    mock_session.get.return_value = None

    room = await get_room_by_id(mock_session, uuid4())

    assert room is None


@pytest.mark.asyncio
async def test_get_existing_schedule_exists():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Schedule()
    mock_session.execute.return_value = mock_result

    schedule = await get_existing_schedule(mock_session, uuid4())

    assert schedule is not None
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_existing_schedule_not_exists():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    schedule = await get_existing_schedule(mock_session, uuid4())

    assert schedule is None


@pytest.mark.asyncio
async def test_create_schedule_and_slots():
    mock_session = AsyncMock()
    room_id = uuid4()
    days_of_week = [1,2,3]
    start_time = time(9,0)
    end_time = time(10,0)

    with patch("src.services.schedule_service.generate_slots_for_schedule") as mock_gen:
        mock_gen.return_value = [MagicMock(), MagicMock()]

        schedule = await create_schedule_and_slots(
            mock_session, room_id, days_of_week, start_time, end_time)

        assert schedule.room_id == room_id
        assert schedule.days_of_week == days_of_week
        assert schedule.start_time == start_time
        assert schedule.end_time == end_time
        mock_session.add.assert_called_once_with(schedule)
        mock_gen.assert_called_once()
        mock_session.add_all.assert_called_once()
        mock_session.flush.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()