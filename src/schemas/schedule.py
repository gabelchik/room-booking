from pydantic import BaseModel, field_validator
from typing import List
from uuid import UUID
from datetime import datetime, time


class ScheduleCreate(BaseModel):
    days_of_week: List[int]
    start_time: str
    end_time: str

    @field_validator("days_of_week")
    def validate_days(cls, v):
        for day in v:
            if day < 1 or day > 7:
                raise ValueError("days_of_week must be between 1 and 7")

        return v

    @field_validator("start_time", "end_time")
    def validate_time(cls, v):
        try:
            time.fromisoformat(v)

        except:
            raise ValueError("time must be in HH:MM format")

        return v


class ScheduleResponse(BaseModel):
    id: UUID
    room_id: UUID
    days_of_week: List[int]
    start_time: time
    end_time: time
