import uuid
from datetime import datetime, timezone, time

from sqlalchemy import String, Integer, DateTime, Time, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                          primary_key=True,
                                          default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String(5),
                                      nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                          primary_key=True,
                                          default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(255),
                                      nullable=False)
    description: Mapped[str | None] = mapped_column(String(500),
                                                    nullable=True)
    size: Mapped[int | None] = mapped_column(Integer,
                                             nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))

    schedule: Mapped["Schedule | None"] = relationship(back_populates="room",
                                                       uselist=False)
    slots: Mapped[list["Slot"]] = relationship(back_populates="room")


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (UniqueConstraint("room_id",
                                       name="unique_room_schedule"))

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                          primary_key=True,
                                          default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                               ForeignKey("rooms.id", ondelete="CASCADE"),
                                               nullable=False)
    days_of_week: Mapped[list[int]] = mapped_column(ARRAY(Integer),
                                                    nullable=False)
    start_time: Mapped[time] = mapped_column(Time(timezone=False),
                                                      nullable=False)
    end_time: Mapped[time] = mapped_column(Time(timezone=False),
                                                    nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))

    room: Mapped["Room"] = relationship(back_populates="schedule")


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (UniqueConstraint("room_id", "start",
                                       name="unique_room_slot_start"))

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                          primary_key=True,
                                          default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                               ForeignKey("rooms.id", ondelete="CASCADE"),
                                               nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                             nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                           nullable=False)
    room: Mapped["Room"] = relationship(back_populates="slots")
    booking: Mapped["Booking | None"] = relationship(back_populates="slot",
                                                     uselist=False)

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                          primary_key=True,
                                          default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("slots.id",
                                                                              ondelete="RESTRICT",
                                                                              nullable=False))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                               ForeignKey("users.id",
                                                          ondelete="RESTRICT"),
                                               nullable=False)
    status: Mapped[str] = mapped_column(String(10),
                                        nullable=False,
                                        default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))
    slot: Mapped["Slot"] = relationship(back_populates="booking")
    user: Mapped["User"] = relationship(back_populates="bookings")