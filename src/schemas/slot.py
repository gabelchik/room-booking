from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

class SlotResponse(BaseModel):
    id: UUID
    room_id: UUID
    start: datetime
    end: datetime