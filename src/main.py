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

from src.services.room_service import RoomService
from src.services.schedule_service import ScheduleService
from src.services.slot_service import SlotService
from src.services.booking_service import BookingService

from src.db.repositories.room_repository import RoomRepository
from src.db.repositories.schedule_repository import ScheduleRepository
from src.db.repositories.slot_repository import SlotRepository
from src.db.repositories.booking_repository import BookingRepository


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
    room_repo = RoomRepository(session)
    room_service = RoomService(room_repo)

    rooms = await room_service.get_all_rooms()

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

    room_repo = RoomRepository(session)
    room_service = RoomService(room_repo)

    new_room = await room_service.create_room()

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

    room_repo = RoomRepository(session)
    schedule_repo = ScheduleRepository(session)
    slot_repo = SlotRepository(session)

    schedule_service = ScheduleService(room_repo, schedule_repo, slot_repo)

    new_schedule = await schedule_service.create_schedule_and_slots(
        room_id=room_id,
        days_of_week = schedule_data.days_of_week,
        start_time = time.fromisoformat(schedule_data.start_time),
        end_time = time.fromisoformat(schedule_data.end_time)
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

    room_repo = RoomRepository(session)
    slot_repo = SlotRepository(session)

    slot_service = SlotService(slot_repo, room_repo)

    slots = await slot_service.get_available_slots_for_date(room_id, target_date)

    return slots


@app.post("/bookings/create", response_model=BookingResponse, status_code=201,
          tags=["Bookings"], description="Create a slot reservation (user only)")
async def create_booking(booking_data: BookingCreate,
                         current_user: dict = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can create bookings")

    booking_repo = BookingRepository(session)
    slot_repo = SlotRepository(session)

    bookings_service = BookingService(booking_repo, slot_repo)

    new_booking = await bookings_service.create_booking(booking_data.slot_id,
                                                        uuid.UUID(current_user["user_id"]))

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

    booking_repo = BookingRepository(session)
    slot_repo = SlotRepository(session)

    booking_service = BookingService(booking_repo, slot_repo)

    booking = await booking_service.cancel_booking(booking_id,
                                                   uuid.UUID(current_user["user_id"]))
    return BookingCancelResponse(id=booking.id, status=booking.status)


@app.get("/bookings/my", response_model=list[BookingResponse],
         tags=["Bookings"], description="List of current user's armor (user only)")
async def get_my_bookings(current_user: dict = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)
):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can view their bookings")

    booking_repo = BookingRepository(session)
    slot_repo = SlotRepository(session)

    booking_service = BookingService(booking_repo, slot_repo)

    bookings = await booking_service.get_user_future_bookings(uuid.UUID(current_user["user_id"]))

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

    booking_repo = BookingRepository(session)
    slot_repo = SlotRepository(session)

    booking_service = BookingService(booking_repo, slot_repo)

    bookings, total = await booking_service.get_all_bookings_paginated(page, page_size)

    return BookingsListResponse(
        bookings=bookings,
        pagination=Pagination(page=page, page_size=page_size, total=total)
    )


@app.get("/_info", status_code=200, tags=["Info"])
async def info():
    return {"status": "ok"}
