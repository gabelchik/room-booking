import pytest
from unittest.mock import AsyncMock, MagicMock

from datetime import date
from uuid import uuid4

from src.core.exceptions import NotFoundError
from src.services.slot_service import SlotService


@pytest.mark.asyncio
async def test_get_available_slots_for_date():
    mock_slot_repo = AsyncMock()
    mock_room_repo = AsyncMock()

    room_id = uuid4()
    target_date = date(2026, 4, 6)
    mock_room_repo.get.return_value = MagicMock()
    mock_slot_repo.get_available_slots_for_date.return_value = [MagicMock(), MagicMock()]

    service = SlotService(mock_slot_repo, mock_room_repo)

    slots = await service.get_available_slots_for_date(room_id, target_date)

    assert len(slots) == 2

    mock_room_repo.get.assert_awaited_once_with(room_id)
    mock_slot_repo.get_available_slots_for_date.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_available_slots_for_date_room_not_found():
    mock_slot_repo = AsyncMock()
    mock_room_repo = AsyncMock()

    mock_room_repo.get.return_value = None
    service = SlotService(mock_slot_repo, mock_room_repo)
    with pytest.raises(NotFoundError):
        await service.get_available_slots_for_date(uuid4(), date.today())