from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class RoomCreate(BaseModel):
    name: str
    description: str | None = None
    size: int | None = None


class RoomResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    size: int | None = None
    created_at:datetime