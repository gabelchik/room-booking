from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class BookingCreate(BaseModel):
    slot_id: UUID


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slot_id: UUID
    user_id: UUID
    status: str
    created_at: datetime


class BookingCancelResponse(BaseModel):
    id: UUID
    status: str


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int

class BookingsListResponse(BaseModel):
    bookings: list[BookingResponse]
    pagination: Pagination