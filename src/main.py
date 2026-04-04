import uuid

from fastapi import FastAPI, Depends

from sqlalchemy import text

from contextlib import asynccontextmanager

from datetime import datetime, time

from zoneinfo import ZoneInfo

from src.services.slot_generator import generate_future_slots_for_schedules
from src.db.session import engine, new_session
from src.db.models import User
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

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.api.tags import tags_metadata

from src.services.user_service import ensure_default_users
from src.services.room_service import get_all_rooms, create_room_s
from src.services.schedule_service import get_room_by_id, get_existing_schedule, create_schedule_and_slots
from src.services.slot_service import get_slot_by_id, get_available_slots_for_date
from src.services.booking_service import (
    has_active_booking, create_booking_s, get_booking_by_id,
    cancel_booking_s, get_user_future_bookings, get_all_bookings_paginated
)


ADMIN_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_UUID = uuid.UUID('22222222-2222-2222-2222-222222222222')


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with new_session() as session:
        await ensure_default_users(session, ADMIN_UUID, USER_UUID)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_future_slots_for_schedules, CronTrigger(hour=3, minute=0, timezone="UTC"))
    scheduler.start()

    yield
    await engine.dispose()


app = FastAPI(title="Room Booking Service",
              description="Сервис бронирования переговорок",
              version="1.0.0",
              openapi_tags=tags_metadata,
              lifespan=lifespan)


@app.post("/dummyLogin", tags=["Auth"])
async def dummy_login(request: DummyLoginSchema):
    if request.role not in ("admin", "user"):
        raise BadRequestError(code="INVALID_REQUEST", message="role must be admin or user")

    user_id = str(ADMIN_UUID) if request.role == "admin" else str(USER_UUID)
    token = create_access_token(data={"sub": user_id, "role": request.role})
    return {"token": token}


@app.get("/rooms", response_model=list[RoomResponse], tags=["Rooms"])
async def list_rooms(current_user: dict = Depends(get_current_user)):
    async with new_session() as session:
        rooms = await get_all_rooms(session)
        return rooms


@app.post("/rooms/create", response_model=RoomResponse, status_code=201, tags=["Rooms"])
async def create_room(room_data: RoomCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise ForbiddenError(code="FORBIDDEN", message="Only admin can create rooms")

    async with new_session() as session:
        new_room = await create_room_s(session, room_data)
        return new_room


@app.post("/rooms/{room_id}/schedule/create", response_model=ScheduleResponse, status_code=201, tags=["Rooms"])
async def create_schedule(
        room_id: uuid.UUID,
        schedule_data: ScheduleCreate,
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise ForbiddenError(code="FORBIDDEN", message="Only admin can create schedules")

    async with new_session() as session:
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


@app.get("/rooms/{room_id}/slots/list", response_model=list[SlotResponse], tags=["Rooms"])
async def list_available_slots(
        room_id: uuid.UUID,
        date: str,
        current_user: dict = Depends(get_current_user)
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise BadRequestError(code="INVALID_REQUEST", message="Invalid date format, use YYYY-MM-DD")

    async with new_session() as session:
        room = await get_room_by_id(session, room_id)
        if not room:
            raise NotFoundError(code="ROOM_NOT_FOUND", message="Room not found")

        slots = await get_available_slots_for_date(session, room_id, target_date)

        return slots


@app.post("/bookings/create", response_model=BookingResponse, status_code=201, tags=["Bookings"])
async def create_booking(booking_data: BookingCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can create bookings")

    async with new_session() as session:
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

@app.post("/bookings/{booking_id}/cancel", response_model=BookingCancelResponse, tags=["Bookings"])
async def cancel_booking(booking_id: uuid.UUID, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can cancel bookings")

    async with new_session() as session:
        booking = await get_booking_by_id(session, booking_id)
        if not booking:
            raise NotFoundError(code="BOOKING_NOT_FOUND", message="Booking not found")

        if booking.user_id != uuid.UUID(current_user["user_id"]):
            raise ForbiddenError(code="FORBIDDEN", message="Can't cancel another user's booking")

        if booking.status == "cancelled":
            return BookingCancelResponse(id=booking.id, status=booking.status)

        booking = await cancel_booking_s(session, booking)
        return BookingCancelResponse(id=booking.id, status=booking.status)


@app.get("/bookings/my", response_model=list[BookingResponse], tags=["Bookings"])
async def get_my_bookings(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "user":
        raise ForbiddenError(code="FORBIDDEN", message="Only users can view their bookings")

    async with new_session() as session:
        bookings = await get_user_future_bookings(session, uuid.UUID(current_user["user_id"]))
        return bookings


@app.get("/bookings/list", response_model=BookingsListResponse, tags=["Bookings"])
async def list_all_bookings(
        page: int = 1,
        page_size: int = 20,
        current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise ForbiddenError(code="FORBIDDEN", message="Only admin can view all bookings")

    if page < 1:
        raise BadRequestError(code="INVALID_REQUEST", message="page must be >= 1")

    if page_size < 1 or page_size > 100:
        raise BadRequestError(code="INVALID_REQUEST", message="pageSize must be between 1 and 100")

    async with new_session() as session:
        bookings, total = await get_all_bookings_paginated(session, page, page_size)

        return BookingsListResponse(
            bookings=bookings,
            pagination=Pagination(page=page, page_size=page_size, total=total)
        )


@app.get("/_info", tags=["Info"])
async def info():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "db": db_status}
