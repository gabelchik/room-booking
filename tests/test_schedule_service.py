import pytest
from unittest.mock import AsyncMock, MagicMock

from uuid import uuid4
from datetime import time

from src.services.schedule_service import ScheduleService
from src.core.exceptions import NotFoundError, ConflictError


@pytest.mark.asyncio
async def test_create_schedule_and_slots_success():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_slot_repo = AsyncMock()

    room_id = uuid4()
    days = [1,2,3]
    start_time = time(9,0)
    end_time = time(10,0)

    mock_room_repo.get.return_value = MagicMock()
    mock_schedule_repo.get_by_room_id.return_value = None
    mock_schedule_repo.add.return_value = MagicMock()
    mock_slot_repo.add_all = AsyncMock()

    service = ScheduleService(mock_room_repo, mock_schedule_repo, mock_slot_repo)
    schedule = await service.create_schedule_and_slots(room_id, days, start_time, end_time)

    assert schedule is not None

    mock_schedule_repo.add.assert_awaited_once()
    mock_slot_repo.add_all.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_schedule_room_not_found():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_slot_repo = AsyncMock()
    mock_room_repo.get.return_value = None

    service = ScheduleService(mock_room_repo, mock_schedule_repo, mock_slot_repo)

    with pytest.raises(NotFoundError):
        await service.create_schedule_and_slots(uuid4(), [], time(9,0), time(10,0))

@pytest.mark.asyncio
async def test_create_schedule_already_exists():
    mock_room_repo = AsyncMock()
    mock_schedule_repo = AsyncMock()
    mock_slot_repo = AsyncMock()
    mock_room_repo.get.return_value = MagicMock()
    mock_schedule_repo.get_by_room_id.return_value = MagicMock()

    service = ScheduleService(mock_room_repo, mock_schedule_repo, mock_slot_repo)

    with pytest.raises(ConflictError):
        await service.create_schedule_and_slots(uuid4(), [], time(9,0), time(10,0))