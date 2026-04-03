import uuid

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text, select

from contextlib import asynccontextmanager

from src.db.session import engine, new_session
from src.db.models import User, Room
from src.core.security import create_access_token
from src.api.dependencies import get_current_user
from src.schemas.auth import DummyLoginSchema
from src.schemas.rooms import RoomCreate, RoomResponse


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
