import pytest
from unittest.mock import AsyncMock, MagicMock

from uuid import uuid4
from datetime import date

from src.services.slot_service import get_slot_by_id, get_available_slots_for_date
from src.db.models import Slot, Booking


@pytest.mark.asyncio
async def test_get_slot_by_id_found():
    mock_session = AsyncMock()
    slot_id = uuid4()
    expected_slot = Slot(id=slot_id)
    mock_session.get.return_value = expected_slot

    slot = await get_slot_by_id(mock_session, slot_id)

    assert slot == expected_slot
    mock_session.get.assert_awaited_once_with(Slot, slot_id)


@pytest.mark.asyncio
async def test_get_slot_by_id_not_found():
    mock_session = AsyncMock()
    mock_session.get.return_value = None

    slot = await get_slot_by_id(mock_session, uuid4())

    assert slot is None


@pytest.mark.asyncio
async def test_get_available_slots_for_date():
    mock_session = AsyncMock()
    room_id = uuid4()
    target_date = date(2026, 4, 6)

    slot1 = Slot()
    slot1.booking = None
    slot2 = Slot()
    slot2.booking = Booking(status="active")
    slot3 = Slot()
    slot3.booking = None

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [slot1, slot2, slot3]
    mock_session.execute.return_value = mock_result

    slots = await get_available_slots_for_date(mock_session, room_id, target_date)

    assert len(slots) == 2
    assert slot1 in slots
    assert slot3 in slots
    assert slot2 not in slots

    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_available_slots_for_date_no_slots():
    mock_session = AsyncMock()
    room_id = uuid4()
    target_date = date(2026, 4, 6)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    slots = await get_available_slots_for_date(mock_session, room_id, target_date)

    assert len(slots) == 0