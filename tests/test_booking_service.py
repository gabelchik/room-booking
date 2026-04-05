import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.services.booking_service import BookingService
from src.db.models import Booking
from src.core.exceptions import NotFoundError, BadRequestError, ConflictError, ForbiddenError

@pytest.mark.asyncio
async def test_create_booking_success():
    mock_booking_repo = AsyncMock()
    mock_slot_repo = AsyncMock()

    slot_id = uuid4()
    user_id = uuid4()
    slot = MagicMock()
    slot.start = datetime.now(ZoneInfo("UTC")) + timedelta(hours=1)

    mock_slot_repo.get.return_value = slot
    mock_booking_repo.has_active_booking.return_value = False
    mock_booking_repo.add.return_value = Booking(slot_id=slot_id, user_id=user_id, status="active")

    service = BookingService(mock_booking_repo, mock_slot_repo)

    booking = await service.create_booking(slot_id, user_id)
    assert booking.status == "active"
    mock_booking_repo.add.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_booking_slot_not_found():
    mock_booking_repo = AsyncMock()
    mock_slot_repo = AsyncMock()
    mock_slot_repo.get.return_value = None

    service = BookingService(mock_booking_repo, mock_slot_repo)

    with pytest.raises(NotFoundError):
        await service.create_booking(uuid4(), uuid4())

@pytest.mark.asyncio
async def test_create_booking_past_slot():
    mock_booking_repo = AsyncMock()
    mock_slot_repo = AsyncMock()

    slot = MagicMock()
    slot.start = datetime.now(ZoneInfo("UTC")) - timedelta(hours=1)

    mock_slot_repo.get.return_value = slot

    service = BookingService(mock_booking_repo, mock_slot_repo)

    with pytest.raises(BadRequestError):
        await service.create_booking(uuid4(), uuid4())

@pytest.mark.asyncio
async def test_create_booking_already_booked():
    mock_booking_repo = AsyncMock()
    mock_slot_repo = AsyncMock()

    slot = MagicMock()
    slot.start = datetime.now(ZoneInfo("UTC")) + timedelta(hours=1)

    mock_slot_repo.get.return_value = slot
    mock_booking_repo.has_active_booking.return_value = True

    service = BookingService(mock_booking_repo, mock_slot_repo)

    with pytest.raises(ConflictError):
        await service.create_booking(uuid4(), uuid4())

@pytest.mark.asyncio
async def test_cancel_booking_success():
    mock_booking_repo = AsyncMock()
    mock_slot_repo = AsyncMock()

    booking = Booking(id=uuid4(), user_id=uuid4(), status="active")

    mock_booking_repo.get.return_value = booking
    mock_booking_repo.update.return_value = booking

    service = BookingService(mock_booking_repo, mock_slot_repo)

    cancelled = await service.cancel_booking(booking.id, booking.user_id)

    assert cancelled.status == "cancelled"
    mock_booking_repo.update.assert_awaited_once_with(booking, status="cancelled")

@pytest.mark.asyncio
async def test_cancel_booking_not_found():
    mock_booking_repo = AsyncMock()
    mock_slot_repo = AsyncMock()
    mock_booking_repo.get.return_value = None

    service = BookingService(mock_booking_repo, mock_slot_repo)

    with pytest.raises(NotFoundError):
        await service.cancel_booking(uuid4(), uuid4())

@pytest.mark.asyncio
async def test_cancel_booking_wrong_user():
    mock_booking_repo = AsyncMock()
    mock_slot_repo = AsyncMock()

    booking = Booking(id=uuid4(), user_id=uuid4(), status="active")

    mock_booking_repo.get.return_value = booking

    service = BookingService(mock_booking_repo, mock_slot_repo)

    with pytest.raises(ForbiddenError):
        await service.cancel_booking(booking.id, uuid4())