
from datetime import datetime, date

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Time, Date, UUID, ARRAY, DateTime
from sqlalchemy.orm import relationship
from app.db import Base


class Holiday(Base):
    __tablename__ = 'holidays'

    date = Column(Date, primary_key=True)
    name = Column(String)


class WorkShift(Base):
    __tablename__ = 'workShifts'

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String)
    days = Column(ARRAY(String), nullable=True)
    start_time = Column(Time)
    end_time = Column(Time)
    flex_time = Column(Time)
    permit_time = Column(Time)
    date = Column(Date, nullable=True)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.now(), nullable=True)
    user_shift = relationship("UserShift", back_populates="shift", cascade="all")


class Event(Base):
    __tablename__ = 'events'

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date)
    start = Column(Time)
    end = Column(Time)
    attendees = Column(ARRAY(UUID))
    created_at = Column(DateTime, default=datetime.now(), nullable=True)
    user_event = relationship("UserEvent", back_populates="event", cascade="all")


class UserShift(Base):
    __tablename__ = 'userShifts'

    user_id = Column(UUID, primary_key=True, index=True)
    shift_id = Column(UUID, ForeignKey('workShifts.id'), primary_key=True)
    shift = relationship("WorkShift", back_populates="user_shift", cascade="all")


class UserEvent(Base):
    __tablename__ = 'userEvents'
    user_id = Column(UUID, primary_key=True, index=True)
    event_id = Column(UUID, ForeignKey('events.id'), primary_key=True)
    event = relationship("Event", back_populates="user_event", cascade="all")


class Log(Base):
    __tablename__ = 'logs'

    id = Column(UUID, primary_key=True, index=True)
    type = Column(String)
    date = Column(Date, default=date.today())
    time = Column(Time)
    comment = Column(String)
    user_id = Column(UUID)
    is_overtime = Column(Boolean)
    approved_overtime = Column(Time)

