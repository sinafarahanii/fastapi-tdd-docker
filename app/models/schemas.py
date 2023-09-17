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
    start: time
    end: time
    flex_time: time = Field(default="00:00")
    permit_time: time
    created_at: datetime = datetime.now()


class ShiftType1(BaseModel):
    name: str
    start: time = Field(default="09:00")
    end: time = Field(default="18:00")
    flex_time: time = Field(default="00:00")
    days:  List[Day]
    permit_time: time = Field(default="04:00")


class ShiftType1Output(ShiftType1):
    id: uuid.UUID
    created_at: datetime = datetime.now()


class ShiftType2(BaseModel):
    name: str
    start: time = Field(default="09:00")
    end: time = Field(default="18:00")
    flex_time: time = Field(default="00:00")
    date: date
    permit_time: time = Field(default="04:00")


class ShiftType2Output(ShiftType2):
    id: uuid.UUID
    created_at: datetime = datetime.now()


class Log(BaseModel):
    log_date: Optional[date]
    time: time
    comment: Optional[str]


class LogOutput(Log):
    id: UUID
    is_overtime: bool
    approved_overtime: time


class Event(BaseModel):
    date: date
    start: time
    end: time
    attendees: list[UUID]


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



