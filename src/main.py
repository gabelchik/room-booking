import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from src.db.session import engine, new_session
from src.db.models import User


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

@app.get("/")
def read_root():
    return {"message": "Hello"}

@app.get("/_info")
async def info():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "db": db_status}