import uuid

from fastapi import FastAPI, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, time

from zoneinfo import ZoneInfo

from src.db.session import get_session
from src.core.security import create_access_token
from src.api.dependencies import get_current_user

from src.schemas.auth import DummyLoginSchema
from src.schemas.room import RoomCreate, RoomResponse
from src.schemas.schedule import ScheduleCreate, ScheduleResponse
from src.schemas.slot import SlotResponse
from src.schemas.booking import (
    BookingCreate, BookingResponse,
    BookingCancelResponse, BookingsListResponse,
    Pagination)

from src.core.exceptions import (
    BadRequestError, ForbiddenError, NotFoundError, ConflictError
)
from src.core.lifespan import lifespan

from src.api.tags import tags_metadata

from src.services.room_service import get_all_rooms, create_room_s
from src.services.schedule_service import get_room_by_id, get_existing_schedule, create_schedule_and_slots
from src.services.slot_service import get_slot_by_id, get_available_slots_for_date
from src.services.booking_service import (
    has_active_booking, create_booking_s, get_booking_by_id,
    cancel_booking_s, get_user_future_bookings, get_all_bookings_paginated
)


ADMIN_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_UUID = uuid.UUID('22222222-2222-2222-2222-222222222222')


app = FastAPI(title="Room Booking Service",
              description="Room Booking Service",
              version="1.0.0",
              openapi_tags=tags_metadata,
              lifespan=lifespan)


@app.post("/dummyLogin", tags=["Auth"],
          description="Issues a test JWT for the specified role (admin/user)")
async def dummy_login(request: DummyLoginSchema):
    if request.role not in ("admin", "user"):
        raise BadRequestError(code="INVALID_REQUEST", message="role must be admin or user")

    user_id = str(ADMIN_UUID) if request.role == "admin" else str(USER_UUID)
    token = create_access_token(data={"sub": user_id, "role": request.role})
    return {"token": token}


@app.get("/rooms", response_model=list[RoomResponse], tags=["Rooms"],
         description="Shows a list of rooms")
async def list_rooms(
        current_user: dict = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    rooms = await get_all_rooms(session)
    return rooms


@app.post("/rooms/create", response_model=RoomResponse, status_code=201,
          tags=["Rooms"], description="Creates a new room")
async def create_room(
        room_data: RoomCreate,
        current_user: dict = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "admin":
        raise ForbiddenError(code="FORBIDDEN", message="Only admin can create rooms")

    new_room = await create_room_s(session, room_data)
    return new_room


@app.post("/rooms/{room_id}/schedule/create", response_model=ScheduleResponse,
          status_code=201, tags=["Rooms"],
          description="Create a meeting schedule (admin only, only once)."
                      "The slot duration is 30 minutes. The schedule cannot be changed after creation")
async def create_schedule(
        room_id: uuid.UUID,
        schedule_data: ScheduleCreate,
        current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "admin":
        raise ForbiddenError(code="FORBIDDEN", message="Only admin can create schedules")

    room = await get_room_by_id(session, room_id)
    if not room:
        raise NotFoundError(code="ROOM_NOT_FOUND", message="Room not found")

    ex_schedule = await get_existing_schedule(session, room_id)
    if ex_schedule:
        raise ConflictError(code="SCHEDULE_EXISTS", message="Schedule already exists for this room")

    start_time = time.fromisoformat(schedule_data.start_time)
    end_time = time.fromisoformat(schedule_data.end_time)
    new_schedule = await create_schedule_and_slots(
        session, room_id, schedule_data.days_of_week, start_time, end_time
    )
    return new_schedule


@app.get("/rooms/{room_id}/slots/list", response_model=list[SlotResponse],
         tags=["Rooms"], description="The list of slots available for booking"
                                     "by appointment and date (admin and user)")
async def list_available_slots(
        room_id: uuid.UUID,
        date: str,
        current_user: dict = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise BadRequestError(code="INVALID_REQUEST", message="Invalid date format, use YYYY-MM-DD")

    room = await get_room_by_id(session, room_id)
    if not room:
        raise NotFoundError(code="ROOM_NOT_FOUND", message="Room not found")

    slots = await get_available_slots_for_date(session, room_id, target_date)

    return slots


@app.post("/bookings/create", response_model=BookingResponse, status_code=201,
          tags=["Bookings"], description="Create a slot reservation (user only)")
async def create_booking(booking_data: BookingCreate,
                         current_user: dict = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can create bookings")

    slot = await get_slot_by_id(session, booking_data.slot_id)
    if not slot:
        raise NotFoundError(code="SLOT_NOT_FOUND", message="Slot not found")

    now = datetime.now(ZoneInfo("UTC"))
    if slot.start < now:
        raise BadRequestError(code="INVALID_REQUEST", message="Can't book a slot in the past")

    if await has_active_booking(session, booking_data.slot_id):
        raise ConflictError(code="SLOT_ALREADY_BOOKED", message="Slot is already booked")

    new_booking = await create_booking_s(session, slot.id, uuid.UUID(current_user["user_id"]))

    return new_booking

@app.post("/bookings/{booking_id}/cancel", response_model=BookingCancelResponse,
          tags=["Bookings"], description="Cancel your reservation"
                                         "(only your own reservation, only the user)")
async def cancel_booking(booking_id: uuid.UUID,
                         current_user: dict = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can cancel bookings")

    booking = await get_booking_by_id(session, booking_id)
    if not booking:
        raise NotFoundError(code="BOOKING_NOT_FOUND", message="Booking not found")

    if booking.user_id != uuid.UUID(current_user["user_id"]):
        raise ForbiddenError(code="FORBIDDEN", message="Can't cancel another user's booking")

    if booking.status == "cancelled":
        return BookingCancelResponse(id=booking.id, status=booking.status)

    booking = await cancel_booking_s(session, booking)
    return BookingCancelResponse(id=booking.id, status=booking.status)


@app.get("/bookings/my", response_model=list[BookingResponse],
         tags=["Bookings"], description="List of current user's armor (user only)")
async def get_my_bookings(current_user: dict = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can view their bookings")

    bookings = await get_user_future_bookings(session, uuid.UUID(current_user["user_id"]))
    return bookings


@app.get("/bookings/list", response_model=BookingsListResponse,
         tags=["Bookings"], description="List of all paginated armor (admin only)")
async def list_all_bookings(
        page: int = 1,
        page_size: int = 20,
        current_user: dict = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "admin":
        raise ForbiddenError(code="FORBIDDEN", message="Only admin can view all bookings")

    if page < 1:
        raise BadRequestError(code="INVALID_REQUEST", message="page must be >= 1")

    if page_size < 1 or page_size > 100:
        raise BadRequestError(code="INVALID_REQUEST", message="pageSize must be between 1 and 100")

    bookings, total = await get_all_bookings_paginated(session, page, page_size)

    return BookingsListResponse(
        bookings=bookings,
        pagination=Pagination(page=page, page_size=page_size, total=total)
    )


@app.get("/_info", status_code=200, tags=["Info"])
async def info():
    return {"status": "ok"}
