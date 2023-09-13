"""""
import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Time, Date, UUID
from sqlalchemy.orm import relationship
from .db import Base


class WorkShift(Base):
    __tablename__ = 'shifts'

    id = Column(UUID, primary_key=True, index=True)
    start_time = Column(Time)
    end_time = Column(Time)


class UserShift(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    shifts = relationship("Shift", back_populates="user")


class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=datetime.date.today())
    time = Column(Time)
    comment = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="logs")

"""""