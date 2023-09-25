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


class ShiftType1(BaseModel):
    name: str = Field(description="Shift name", default="daily shift")
    start: time = Field(description="Start time", default="09:00")
    end: time = Field(description="End time", default="18:00")
    flex_time: time = Field(description="Flex time", default="01:00")
    days:  List[Day] = Field(description="Days of the week", default=[
                            "1",
                            "2",
                            "3",
                            "4",
                            "5"
                        ],)
    permit_time: time = Field(description="Permit time", default="04:00")


class ShiftType1Output(ShiftType1):
    id: uuid.UUID


class ShiftType2(BaseModel):
    name: str = Field(description="Shift name", default="NIGHT shift")
    start: time = Field(description="Start time", default="19:00")
    end: time = Field(description="End time", default="21:00")
    flex_time: time = Field(description="Flex time", default="00:15")
    date: date
    permit_time: time = Field(description="Permit time", default="01:00")


class ShiftType2Output(ShiftType2):
    id: uuid.UUID


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
    presenter: str = Field(description="Event resenter", default="Mr.beast")
    name: str = Field(description="Event name", default="Anniversary meeting")
    date: date
    start: time = Field(description="Event start time", default="15:00")
    end: time = Field(description="Event end time", default="18:00")
    attendees: list[UUID]


class EventOutput(Event):
    id: UUID


class Holiday(BaseModel):
    name: str = Field(default="christmas")
    date: date


class DailyWork(BaseModel):
    date: date
    hours: str


class UserShift(BaseModel):
    user_id: UUID
    shift_id: UUID
    activation: date
    expiration: date
    is_expired: bool
