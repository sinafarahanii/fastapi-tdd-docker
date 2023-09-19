import uuid
from uuid import UUID, uuid4
from datetime import datetime, time, date
import enum
from typing import Optional, List
from pydantic import BaseModel, Field


class Type(str, enum.Enum):
    one = "1"
    two = "2"


class Day(str, enum.Enum):
    MONDAY = "1"
    TUESDAY = "2"
    WEDNESDAY = "3"
    THURSDAY = "4"
    FRIDAY = "5"
    SATURDAY = "6"
    SUNDAY = "7"


class Shift(BaseModel):
    id: uuid.UUID
    name: str
    days: Optional[list[Day]]
    type: Type
    date: Optional[date]
    start_time: time
    end_time: time
    flex_time: time
    permit_time: time
    created_at: datetime = datetime.now()


class ShiftType1(BaseModel):
    name: str = Field(description="Shift name")
    start: time = Field(description="Start time")
    end: time = Field(description="End time")
    flex_time: time = Field(description="Flex time")
    days:  List[Day] = Field(description="Days of the week")
    permit_time: time = Field(description="Permit time")


class ShiftType1Output(ShiftType1):
    id: uuid.UUID
    created_at: datetime = datetime.now()


class ShiftType2(BaseModel):
    name: str = Field(description="Shift name")
    start: time = Field(description="Start time")
    end: time = Field(description="End time")
    flex_time: time = Field(description="Flex time")
    date: date
    permit_time: time = Field(description="Permit time")


class ShiftType2Output(ShiftType2):
    id: uuid.UUID
    created_at: datetime = datetime.now()


class Log(BaseModel):
    date: Optional[date]
    time: time
    comment: Optional[str]


class LogOutput(Log):
    id: UUID
    user_id: UUID
    is_overtime: bool
    approved_overtime: time
    type: str


class Event(BaseModel):
    name: str = Field(description="Event name")
    date: date
    start: time = Field(description="Event start time")
    end: time = Field(description="Event end time")
    attendees: list[UUID] = Field(description="Event attendees")


class EventOutput(Event):
    id: UUID


class User(BaseModel):
    id: uuid.UUID
    shifts: list[Shift]
    entry_logs: list[LogOutput]
    exit_logs: list[LogOutput]
    created_at: datetime = datetime.now()


class Holiday(BaseModel):
    name: str
    date: date


class DailyWork(BaseModel):
    date: date
    hours: str



