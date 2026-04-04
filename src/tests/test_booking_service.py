import pytest
from unittest.mock import AsyncMock, MagicMock

from uuid import uuid4

from src.services.booking_service import (
    get_booking_by_id,
    has_active_booking,
    create_booking_s,
    cancel_booking_s,
    get_user_future_bookings,
    get_all_bookings_paginated
)
from src.db.models import Booking


@pytest.mark.asyncio
async def test_get_booking_by_id_found():
    mock_session = AsyncMock()
    booking_id = uuid4()
    expected_booking = Booking(id=booking_id)
    mock_session.get.return_value = expected_booking

    booking = await get_booking_by_id(mock_session, booking_id)

    assert booking == expected_booking
    mock_session.get.assert_awaited_once_with(Booking, booking_id)


@pytest.mark.asyncio
async def test_get_booking_by_id_not_found():
    mock_session = AsyncMock()
    mock_session.get.return_value = None

    booking = await get_booking_by_id(mock_session, uuid4())

    assert booking is None


@pytest.mark.asyncio
async def test_has_active_booking_true():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Booking(status="active")
    mock_session.execute.return_value = mock_result

    result = await has_active_booking(mock_session, uuid4())

    assert result is not None


@pytest.mark.asyncio
async def test_has_active_booking_false():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await has_active_booking(mock_session, uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_create_booking():
    mock_session = AsyncMock()
    slot_id = uuid4()
    user_id = uuid4()

    booking = await create_booking_s(mock_session, slot_id, user_id)

    assert booking.slot_id == slot_id
    assert booking.user_id == user_id
    assert booking.status == "active"

    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_cancel_booking():
    mock_session = AsyncMock()

    cancelled = await cancel_booking_s(mock_session,
                                       Booking(status="active"))

    assert cancelled.status == "cancelled"

    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_future_bookings():
    mock_session = AsyncMock()
    user_id = uuid4()
    future_booking = Booking()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [future_booking]
    mock_session.execute.return_value = mock_result

    bookings = await get_user_future_bookings(mock_session, user_id)

    assert len(bookings) == 1

    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_bookings_paginated():
    mock_session = AsyncMock()
    mock_session.scalar.return_value = 100
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [Booking() for _ in range(20)]
    mock_session.execute.return_value = mock_result

    bookings, total = await get_all_bookings_paginated(mock_session, page=2, page_size=20)

    assert total == 100
    assert len(bookings) == 20

    mock_session.scalar.assert_awaited_once()
    mock_session.execute.assert_awaited_once()