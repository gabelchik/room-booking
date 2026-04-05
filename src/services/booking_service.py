import uuid

from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.models import Booking
from src.db.repositories.booking_repository import BookingRepository
from src.db.repositories.slot_repository import SlotRepository
from src.core.exceptions import NotFoundError, BadRequestError, ConflictError, ForbiddenError


class BookingService:
    def __init__(self, booking_repo: BookingRepository, slot_repo: SlotRepository):
        self.booking_repo = booking_repo
        self.slot_repo = slot_repo

    async def create_booking(self, slot_id: uuid.UUID, user_id: uuid.UUID) -> Booking:
        slot = await self.slot_repo.get(slot_id)
        if not slot:
            raise NotFoundError(code="SLOT_NOT_FOUND", message="Slot not found")

        now = datetime.now(ZoneInfo("UTC"))
        if slot.start < now:
            raise BadRequestError(code="INVALID_REQUEST", message="Can't book a slot in the past")

        if await self.booking_repo.has_active_booking(slot_id):
            raise ConflictError(code="SLOT_ALREADY_BOOKED", message="Slot is already booked")
        new_booking = Booking(slot_id=slot_id, user_id=user_id, status="active")
        return await self.booking_repo.add(new_booking)

    async def cancel_booking(self, booking_id: uuid.UUID, user_id: uuid.UUID) -> Booking:
        booking = await self.booking_repo.get(booking_id)
        if not booking:
            raise NotFoundError(code="BOOKING_NOT_FOUND", message="Booking not found")

        if booking.user_id != user_id:
            raise ForbiddenError(code="FORBIDDEN", message="Can't cancel another user's booking")

        if booking.status == "cancelled":
            return booking

        return await self.booking_repo.update(booking, status="cancelled")

    async def get_user_future_bookings(self, user_id: uuid.UUID) -> list[Booking]:
        now = datetime.now(ZoneInfo("UTC"))
        return await self.booking_repo.get_user_future_bookings(user_id, now)

    async def get_all_bookings_paginated(self, page: int, page_size: int):
        return await self.booking_repo.get_all_paginated(page, page_size)