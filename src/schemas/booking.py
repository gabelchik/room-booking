from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class BookingCreate(BaseModel):
    slot_id: UUID


class BookingResponse(BaseModel):
    id: UUID
    slot_id: UUID
    user_id: UUID
    status: str
    created_at: datetime


class BookingCancelResponse(BaseModel):
    id: UUID
    status: str
