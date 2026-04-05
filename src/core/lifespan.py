from fastapi import FastAPI
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.db.session import engine, new_session
from src.db.repositories.user_repository import UserRepository
from src.services.user_service import UserService
from src.services.slot_generator import generate_future_slots_for_schedules
import uuid


ADMIN_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_UUID = uuid.UUID('22222222-2222-2222-2222-222222222222')


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with new_session() as session:
        user_repo = UserRepository(session)
        user_service = UserService(user_repo)
        await user_service.ensure_default_users(ADMIN_UUID, USER_UUID)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_future_slots_for_schedules, CronTrigger(hour=3, minute=0, timezone="UTC"))
    scheduler.start()

    yield
    scheduler.shutdown()
    await engine.dispose()