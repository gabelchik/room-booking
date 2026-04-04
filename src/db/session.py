from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

new_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session():
    async with new_session() as session:
        async with session.begin():
            yield session