
from datetime import datetime, date
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Time, Date, UUID, ARRAY, DateTime, func
from sqlalchemy.orm import relationship, declarative_mixin
from sqlalchemy_utc import UtcDateTime
from app.db import Base


@declarative_mixin
class BaseModel:
    """
    Base model for common columns in database tables.

    This mixin class provides common columns like 'creator', 'created', and 'last_updated'
    to be used in other SQLAlchemy models.
    """

    creator = Column(String(36), nullable=False)
    created = Column(UtcDateTime, nullable=False, default=func.now())
    last_updated = Column(UtcDateTime, nullable=False, default=func.now())


class Holiday(Base):
    __tablename__ = 'holidays'

    date = Column(Date, primary_key=True)
    name = Column(String)
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())


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
    user_shift = relationship("UserShift", back_populates="shift", cascade="all")
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())


class Event(Base):
    __tablename__ = 'events'

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date)
    start = Column(Time)
    end = Column(Time)
    attendees = Column(ARRAY(UUID))
    user_event = relationship("UserEvent", back_populates="event", cascade="all")
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())


class UserShift(Base):
    __tablename__ = 'userShifts'

    user_id = Column(UUID, primary_key=True, index=True)
    shift_id = Column(UUID, ForeignKey('workShifts.id'), primary_key=True)
    activation = Column(Date)
    expiration = Column(Date, nullable=True, default=date.max)
    is_expired = Column(Boolean, default=False)
    shift = relationship("WorkShift", back_populates="user_shift", cascade="all")
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())


class UserEvent(Base):
    __tablename__ = 'userEvents'
    user_id = Column(UUID, primary_key=True, index=True)
    event_id = Column(UUID, ForeignKey('events.id'), primary_key=True)
    event = relationship("Event", back_populates="user_event", cascade="all")
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())


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
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

