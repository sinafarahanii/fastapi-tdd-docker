
from datetime import datetime, date

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Time, Date, UUID, ARRAY
from sqlalchemy.orm import relationship
from app.db import Base


class Holiday(Base):
    __tablename__ = 'holidays'

    date = Column(Date, primary_key=True)
    name = Column(String)


class WorkShift(Base):
    __tablename__ = 'shifts'

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String)
    days = Column(ARRAY(String), nullable=True)
    start_time = Column(Time)
    end_time = Column(Time)
    flex_time = Column(Time)
    permit_time = Column(Time)
    date = Column(Date, nullable=True)
    type = Column(String)
    created_at = Column(Time, default=datetime.now())


class Event(Base):
    __tablename__ = 'events'

    id = Column(UUID, primary_key=True, index=True)
    presenter = Column(String)
    date = Column(Date)
    start = Column(Time)
    end = Column(Time)


class UserShift(Base):
    __tablename__ = 'userShifts'

    user_id = Column(UUID, primary_key=True, index=True)
    shift_id = Column(UUID, primary_key=True)


class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=date.today())
    time = Column(Time)
    comment = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_overtime = Column(Boolean)
    approved_overtime = Column(Time)
    user = relationship("User", back_populates="logs")

