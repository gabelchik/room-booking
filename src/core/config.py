import os
from src.core.exceptions import ApplicationError
from pydantic_settings import BaseSettings

def get_db_url() -> str:
    db_user = os.getenv("DB_USER", "")
    db_pswd = os.getenv("DB_PSWD", "")
    db_host = os.getenv("DB_HOST", "")
    db_port = os.getenv("DB_PORT", "")
    db_name = os.getenv("DB_NAME", "")
    if not all([db_user, db_pswd, db_host, db_port, db_name]):
        raise ApplicationError("You should provide db credentials")

    return f"postgresql+asyncpg://{db_user}:{db_pswd}@{db_host}:{db_port}/{db_name}"


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = get_db_url()

settings = Settings()