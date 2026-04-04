import uuid
import pytest_asyncio

from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.db.base import Base
from src.db.session import get_session
from src.main import app
from src.services.user_service import ensure_default_users


ADMIN_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_UUID = uuid.UUID("22222222-2222-2222-2222-222222222222")


TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@db_test:5432/room_booking_test"

engine_test = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = async_sessionmaker(
    engine_test,
    expire_on_commit=False,
    class_=AsyncSession)


async def override_get_session():
    async with TestingSessionLocal() as session:
        async with session.begin():
            yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        async with session.begin():
            await ensure_default_users(session, ADMIN_UUID, USER_UUID)
    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator:
    async with TestingSessionLocal() as session:
        async with session.begin():
            yield session
