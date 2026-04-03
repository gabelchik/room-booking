import uuid

from fastapi import FastAPI, HTTPException, Depends

from sqlalchemy import text, select

from contextlib import asynccontextmanager

from datetime import datetime, date, time, timedelta

from zoneinfo import ZoneInfo

from sqlalchemy.orm import selectinload

from src.services.slot_generator import generate_slots_for_schedule, generate_future_slots_for_schedules

from src.db.session import engine, new_session
from src.db.models import User, Room, Schedule, Slot, Booking
from src.core.security import create_access_token
from src.api.dependencies import get_current_user
from src.schemas.auth import DummyLoginSchema
from src.schemas.rooms import RoomCreate, RoomResponse
from src.schemas.schedule import ScheduleCreate, ScheduleResponse
from src.schemas.slot import SlotResponse

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


ADMIN_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_UUID = uuid.UUID('22222222-2222-2222-2222-222222222222')


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with new_session() as session:
        admin = await session.get(User, ADMIN_UUID)
        if not admin:
            session.add(User(id=ADMIN_UUID, role="admin"))
        user = await session.get(User, USER_UUID)
        if not user:
            session.add(User(id=USER_UUID, role="user"))
        await session.commit()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_future_slots_for_schedules, CronTrigger(hour=0, minute=10))
    scheduler.start()

    yield
    await engine.dispose()


app = FastAPI(title="Room booking Service", lifespan=lifespan)


@app.post("/dummyLogin")
async def dummy_login(request: DummyLoginSchema):
    if request.role not in ("admin", "user"):
        raise HTTPException(status_code=400,
        detail={"error": {"code": "INVALID_REQUEST",
                          "message": "role must be admin or user"}}
        )

    user_id = str(ADMIN_UUID) if request.role == "admin" else str(USER_UUID)
    token = create_access_token(data={"sub": user_id, "role": request.role})
    return {"token": token}


@app.get("/rooms", response_model=list[RoomResponse])
async def list_rooms(current_user: dict = Depends(get_current_user)):
    async with new_session() as session:
        query = select(Room).order_by(Room.created_at)
        result = await session.execute(query)
        rooms = result.scalars().all()
        return rooms


@app.post("/rooms/create", response_model=RoomResponse, status_code=201)
async def create_room(room_data: RoomCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "FORBIDDEN",
                              "message": "Only admin can create rooms"}}
        )

    async with new_session() as session:
        new_room = Room(
            name=room_data.name,
            description=room_data.description,
            size=room_data.size
        )
        session.add(new_room)
        await session.commit()
        await session.refresh(new_room)
        return new_room


@app.post("/rooms/{room_id}/schedule/create",
          response_model=ScheduleResponse, status_code=201)
async def create_schedule(
        room_id: uuid.UUID,
        schedule_data: ScheduleCreate,
        current_user: dict = Depends(get_current_user)
        ):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "FORBIDDEN",
                              "message": "Only admin can create schedules"}}
        )

    async with new_session() as session:
        room = await session.get(Room, room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "ROOM_NOT_FOUND",
                                  "message": "Room not found"}}
            )

        query = select(Schedule).where(Schedule.room_id == room_id)
        result = await session.execute(query)
        ex_schedule = result.scalar_one_or_none()
        if ex_schedule:
            raise HTTPException(
                status_code=409,
                detail={"error": {"code": "SCHEDULE_EXISTS",
                                  "message": "Schedule already exists for this room"}}
            )

        start_time = time.fromisoformat(schedule_data.start_time)
        end_time = time.fromisoformat(schedule_data.end_time)
        new_schedule = Schedule(
            room_id = room_id,
            days_of_week = schedule_data.days_of_week,
            start_time = start_time,
            end_time = end_time,
        )

        session.add(new_schedule)

        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        slots = generate_slots_for_schedule(new_schedule, start_date, end_date)

        session.add_all(slots)

        await session.commit()
        await session.refresh(new_schedule)

        return new_schedule


@app.get("/rooms/{room_id}/slots/list", response_model=list[SlotResponse])
async def list_available_slots(
        room_id: uuid.UUID,
        date: str,
        current_user: dict = Depends(get_current_user)
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_REQUEST",
                              "message": "Invalid date format, use YYYY-MM-DD"}}
        )

    async with new_session() as session:
        room = await session.get(Room, room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "ROOM_NOT_FOUND",
                                  "message": "Room not found"}}
            )

    start_day = datetime.combine(
        target_date, datetime.min.time()).replace(tzinfo=ZoneInfo("UTC"))
    end_day = start_day + timedelta(days=1)

    query = select(Slot).options(selectinload(Slot.booking)).where(
        Slot.room_id == room_id,
        Slot.start >= start_day,
        Slot.start < end_day
    ).order_by(Slot.start)
    result = await session.execute(query)
    slots = result.scalars().all()

    available_slots = []
    for slot in slots:
        if not slot.booking or slot.booking.status != "active":
            available_slots.append(slot)

    return available_slots


@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['role']} with id {current_user['user_id']}"}


@app.get("/_info")
async def info():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "db": db_status}
