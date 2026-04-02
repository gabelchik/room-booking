import uuid

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text

from contextlib import asynccontextmanager

from src.db.session import engine, new_session
from src.db.models import User
from src.core.security import create_access_token
from src.api.dependencies import get_current_user


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


class DummyLoginSchema(BaseModel):
    role: str


@app.post("/dummyLogin")
async def dummy_login(request: DummyLoginSchema):
    if request.role not in ("admin", "user"):
        raise HTTPException(status_code=400,detail=
        {"error": {"code": "INVALID_REQUEST", "message": "role must be admin or user"}}
        )

    user_id = str(ADMIN_UUID) if request.role == "admin" else str(USER_UUID)
    token = create_access_token(data={"sub": user_id, "role": request.role})
    return {"token": token}


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
