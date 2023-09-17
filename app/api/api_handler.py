import datetime
from humanfriendly import format_timespan
import uuid
from typing import List, Annotated
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine
from fastapi import APIRouter, Path, Query, Request, middleware, HTTPException, Body, Depends
from app.models import models
from fastapi.responses import RedirectResponse
from app.models.schemas import Shift, User, Type, Day, Holiday, Log, LogOutput, ShiftType1, ShiftType2, DailyWork, ShiftType1Output, ShiftType2Output, Event, EventOutput
from datetime import date, time, timedelta
from ortools.sat.python import cp_model
import pandas

models.Base.metadata.create_all(bind=engine)
router = APIRouter()

events = []

users = [
     User(id=uuid.uuid4(), shifts=[], entry_logs=[], exit_logs=[])
]

shifts = [Shift(name="shift", type="1", start="09:00", end="18:00", flex_time="01:00", days=[Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY, Day.SATURDAY, Day.SUNDAY], id=uuid.uuid4(), date=None, permit_time="04:00"),
          Shift(name="shift", type="2", start="12:00", end="15:00", flex_time="00:30", days=None, id=uuid.uuid4(), date="2023-10-10", permit_time="04:00"),
          Shift(name="shift", type="2", start="13:00", end="16:00", flex_time="00:30", days=None, id=uuid.uuid4(), date="2023-10-10", permit_time="04:00"),
          Shift(name="shift", type="1", start="11:00", end="19:00", flex_time="01:00", days=[Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY], id=uuid.uuid4(), date=None, permit_time="04:00")]

holidays = []


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/holidays", response_model=List[Holiday], tags=["Holidays"], status_code=201)
async def create_holidays(holiday_list: List[Holiday], db: Session = Depends(get_db)):
    holiday_list = db.query(models.Holiday).all()
    """""
    for holiday in holidays:
        if holiday_list.__contains__(holiday.date):
            holiday_list.remove(holiday)
    """""
    for h in holiday_list:
        holiday = models.Holiday(date=h.date, name=h.name)
        db.add(holiday)
        db.commit()
        db.refresh(holiday)
    return holiday_list


@router.get("/holidays", response_model=list[Holiday], tags=["Holidays"])
async def get_holidays(start: date = Query(None, title="start date"), end: date = Query(None, title="end date"), db: Session = Depends(get_db)):
    if start is None and end is None:
        raise HTTPException(status_code=400, detail="No parameter provided!")
    if start is None:
        start = end
    if end is None:
        end = start
    if end < start:
        raise HTTPException(status_code=422, detail="End date can't be before start date!")
    output_holidays = []
    holidays = db.query(models.Holiday).all()
    for holiday in holidays:
        if holiday.date >= start <= end:
            output_holidays.append(holiday)
    return output_holidays


@router.delete("/holidays", response_model=Holiday, tags=["Holidays"])
async def delete_holidays(date: date, db: Session = Depends(get_db)):

    holiday_list = db.query(models.Holiday).all()
    for holiday in holiday_list:
        if date == holiday.date:
            db.delete(holiday)
            db.commit()
            db.refresh(holiday)
            return holiday
    raise HTTPException(status_code=404, detail="There is no holiday on these dates!")


@router.put("/holidays", response_model=Holiday, tags=["Holidays"])
async def update_holiday(holiday_date: date, new_date: date = Query(None), new_name: str = Query(None),  db: Session = Depends(get_db)):
    if not new_date and not new_name:
        raise HTTPException(status_code=400, detail="You most provide information!")
    holidays = db.query(models.Holiday).all()
    target_holiday = db.query(models.Holiday).filter(models.Holiday.date == holiday_date).first()
    for holiday in holidays:
        if holiday.date == holiday_date:
            if new_name is not None:
                target_holiday.name = new_name
            if new_date is not None:
                target_holiday.date = new_date
            return holiday
    raise HTTPException(status_code=404, detail="There is no holiday on this date!")


@router.patch("/holidays", response_model=Holiday, tags=["Holidays"])
async def update_holiday(holiday_date: date, new_date: date = Query(None), new_name: str = Query(None)):
    if not new_date and not new_name:
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    for holiday in holidays:
        if holiday.date == holiday_date:
            if new_name is not None:
                holiday.name = new_name
            if new_date is not None:
                holiday.date = new_date
            return holiday
    raise HTTPException(status_code=404, detail="There is no holiday on this date!")


@router.get("/workShifts", response_model=list[Shift], tags=["WorkShift"])
async def get_shifts():
    return shifts


@router.delete("/workShifts", response_model=Shift, tags=["WorkShift"])
async def delete_shift(shift_id: uuid.UUID):
    for shift in shifts:
        if shift.id == shift_id:
            shifts.remove(shift)
            return shift
    raise HTTPException(status_code=404, detail=f"There is no shift with id={shift_id}")


@router.delete("/userShifts", response_model=Shift, tags=["UserShift"])
async def delete_user_shift(user_id: uuid.UUID, shift_id: uuid.UUID):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    for shift in target_user.shifts:
        if shift.id == shift_id:
            target_user.shifts.remove(shift)
            return shift
    raise HTTPException(status_code=404, detail=f"There is no shift with id={shift_id}")


@router.patch("/workShifts/type1", response_model=ShiftType1Output, tags=["WorkShift"])
async def update_shift_type1(shift_id: uuid.UUID, start: time | None = None,  end: time | None = None,  flex_time: time | None = None, permit_time: time | None = None,  days: List[Day] = Query(None)):
    target_shift = None
    for shift in shifts:
        if shift.id == shift_id:
            target_shift = shift
    if target_shift is None:
        raise HTTPException(status_code=404, detail=f"Shift with id={shift_id} doesn't exist!")
    if target_shift.type == "2":
        raise HTTPException(status_code=409, detail="This shift is a type2 shift!")
    if all(info is None for info in (start, end, flex_time, permit_time, days)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    if start is not None:
        target_shift.start = start
    if end is not None:
        target_shift.end = end
    if flex_time is not None:
        target_shift.flex_time = flex_time
    if permit_time is not None:
        target_shift.permit_time = permit_time
    if days is not None:
        target_shift.days = days
    return target_shift


@router.patch("/workShifts/type2", response_model=Shift, tags=["WorkShift"])
async def update_shift_type2(shift_id: uuid.UUID, start: time | None = None,  end: time | None = None,  flex_time: time | None = None, permit_time: time | None = None, date: date | None = None):
    target_shift = None
    for shift in shifts:
        if shift.id == shift_id:
            target_shift = shift
    if target_shift is None:
        raise HTTPException(status_code=404, detail=f"Shift with id={shift_id} doesn't exist!")
    if target_shift.type == "1":
        raise HTTPException(status_code=409, detail="This shift is a type1 shift!")
    if all(info is None for info in (start, end, flex_time, permit_time, date)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    if start is not None:
        target_shift.start = start
    if end is not None:
        target_shift.end = end
    if flex_time is not None:
        target_shift.flex_time = flex_time
    if permit_time is not None:
        target_shift.permit_time = permit_time
    if date is not None:
        target_shift.date = date
    return target_shift


@router.get("/userShifts", response_model=list[Shift], tags=["UserShift"])
def get_user_shifts(user_id: uuid.UUID):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    return  target_user.shifts


@router.post("/workShifts/type1", response_model=ShiftType1Output, tags=["WorkShift"], status_code=201)
async def create_shift_type1(shift: ShiftType1):
    if shift.end < shift.start:
        raise HTTPException(status_code=422, detail="end time can't be before start time")
    id = uuid.uuid4()
    pending_shift = Shift(name=shift.name, days=shift.days, type=Type.one, start=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end=shift.end, date=None, id=id)
    output_shift = ShiftType1Output(name=shift, days=shift.days, type=Type.one, start=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end=shift.end, id=id)
    shifts.append(pending_shift)
    return output_shift


@router.post("/workShifts/type2", response_model=ShiftType2Output, tags=["WorkShift"], status_code=201)
async def create_shift_type2(shift: ShiftType2):
    if shift.date < date.today():
        raise HTTPException(status_code=422, detail="Shift date can't be in the past")
    if shift.end < shift.start:
        raise HTTPException(status_code=422, detail="end time can't be before start time")
    id = uuid.uuid4()
    pending_shift = Shift(name=shift.name, days=None, type=Type.two, start=shift.start, flex_time=shift.flex_time,  permit_time=shift.permit_time, end=shift.end, date=shift.date, id=id)
    output_shift = ShiftType2Output(name=shift.name, date=shift.date, type=Type.one, start=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end=shift.end, id=id)
    shifts.append(pending_shift)
    return output_shift


@router.post("/userShifts", response_model=Shift, tags=["UserShift"], status_code=201)
async def add_user_shift(user_id: uuid.UUID, shift_id: uuid.UUID):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    user_shifts = target_user.shifts
    pending_shift = ""
    for find_shift in shifts:
        if find_shift.id == shift_id:
            pending_shift = find_shift
    if not pending_shift:
        raise HTTPException(status_code=404, detail=f"Shift with id={shift_id} doesn't exist!")
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    overlap_check = list()
    pending_shift_start = pending_shift.start.hour * 60 + pending_shift.start.minute
    pending_shift_end = pending_shift.end.hour * 60 + pending_shift.end.minute
    for shift in user_shifts:
        if shift.id == shift_id:
            raise HTTPException(status_code=409, detail="User has this shift already!")
        shift_start = shift.start.hour * 60 + shift.start.minute
        shift_end = shift.end.hour * 60 + shift.end.minute
        if shift.type == "1":
            if pending_shift.type == "1":
                for day in pending_shift.days:
                    if day in shift.days:
                        i0 = model.NewIntervalVar(pending_shift_start, pending_shift_end-pending_shift_start,
                                                  pending_shift_end, 'i0')
                        i1 = model.NewIntervalVar(shift_start, shift_end-shift_start, shift_end, 'i1')
                        overlap_check.append(i0)
                        overlap_check.append(i1)
            if pending_shift.type == "2":
                days = list()
                for day in shift.days:
                    days.append(int(day.value))
                if pending_shift.date.today().weekday()+1 in days:
                    local_overlap_check = list()
                    local_model = cp_model.CpModel()
                    local_solver = cp_model.CpSolver()
                    i0 = local_model.NewIntervalVar(pending_shift_start, pending_shift_end - pending_shift_start,
                                              pending_shift_end, 'i0')
                    i1 = local_model.NewIntervalVar(shift_start, shift_end - shift_start, shift_end, 'i1')
                    local_overlap_check.append(i0)
                    local_overlap_check.append(i1)
                    local_model.AddNoOverlap(local_overlap_check)
                    status = local_solver.Solve(model=local_model)
                    if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
                        raise HTTPException(status_code=409,
                                            detail="Shift can't be scheduled because it is in conflict with another type 1 shift!")
        if shift.type == "2":
            if pending_shift.type == "2":
                if shift.date == pending_shift.date:
                    i0 = model.NewIntervalVar(pending_shift_start, pending_shift_end - pending_shift_start,
                                              pending_shift_end, 'i0')
                    i1 = model.NewIntervalVar(shift_start, shift_end - shift_start, shift_end, 'i1')
                    overlap_check.append(i0)
                    overlap_check.append(i1)
            if pending_shift.type == "1":
                days = list()
                for day in pending_shift.days:
                    days.append(int(day.value))
                if shift.date.today().weekday()+1 in days:
                    local_overlap_check = list()
                    local_model = cp_model.CpModel()
                    local_solver = cp_model.CpSolver()
                    i0 = local_model.NewIntervalVar(pending_shift_start, pending_shift_end - pending_shift_start,
                                              pending_shift_end, 'i0')
                    i1 = local_model.NewIntervalVar(shift_start, shift_end - shift_start, shift_end, 'i1')
                    local_overlap_check.append(i0)
                    local_overlap_check.append(i1)
                    local_model.AddNoOverlap(local_overlap_check)
                    status = local_solver.Solve(model=local_model)
                    if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
                        user_shifts.remove(shift)
                        user_shifts.append(pending_shift)
                        return pending_shift

        model.AddNoOverlap(overlap_check)
        status = solver.Solve(model=model)
        if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
            raise HTTPException(status_code=409,
                                detail="Shift can't be scheduled because it is in conflict with another same type shift!")
    user_shifts.append(pending_shift)
    target_user.shifts = user_shifts
    return pending_shift


@router.post("/events", response_model=EventOutput, tags=["Event"], status_code=201)
async def create_event(event: Event):
    for holiday in holidays:
        if holiday.date == event.date:
            raise HTTPException(status_code=409, detail=f"{event.date} is a holiday!")
    users_id = []
    for user in users:
        users_id.append(user.id)
    for user_id in event.attendees:
        if not users_id.__contains__(user_id):
            raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist")
    if event.start > event.end:
        raise HTTPException(status_code=422, detail="End time can't be before start time.")
    pending_event = EventOutput(date=event.date, start=event.start, end=event.end, attendees=event.attendees, id=uuid.uuid4())
    events.append(pending_event)
    return pending_event


@router.get("/users/events", response_model=list[EventOutput], tags=["Event"])
async def get_user_events(user_id: uuid.UUID):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    user_events = []
    for event in events:
        if event.attendees.__contains__(user_id):
            user_events.append(event)
    return user_events


@router.get("/events", response_model=list[EventOutput], tags=["Event"])
async def get_events():
    return events


@router.delete("/events", response_model=EventOutput, tags=["Event"])
async def delete_event(event_id: uuid.UUID):
    for event in events:
        if event.id == event_id:
            events.remove(event)
            return event
    raise HTTPException(status_code=404, detail=f"Event with id={event_id} doesn't exist")


@router.patch("/events", response_model=EventOutput, tags=["Event"])
async def patch_event(event_id: uuid.UUID, attendees: list[uuid.UUID], date: date | None = None, start: time | None = None, end: time | None = None):
    if all(info is None for info in (end, start, attendees, date)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    for event in events:
        if event.id == event_id:
            if date is not None:
                event.date = date
            if start is not None:
                event.start = start
            if end is not None:
                event.end = end
            if attendees is not None:
                event.attendees = attendees
            return event

    raise HTTPException(status_code=404, detail=f"Event with id={event_id} doesn't exist")


@router.get("/users/logs", response_model=list[list[LogOutput]], tags=["Log"])
async def get_user_logs(user_id: uuid.UUID):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    output_logs = []
    output_logs.append(target_user.entry_logs)
    output_logs.append(target_user.exit_logs)
    return output_logs


@router.delete("/users/logs", response_model=LogOutput, tags=["Log"])
async def delete_user_logs(user_id: uuid.UUID, log_id: uuid.UUID):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    for entry_log in target_user.entry_logs:
        if entry_log.id == log_id:
            target_user.entry_logs.remove(entry_log)
            return entry_log
    for exit_log in target_user.exit_logs:
        if exit_log.id == log_id:
            target_user.exit_logs.remove(exit_log)
            return exit_log
    raise HTTPException(status_code=404, detail=f"Log with id={log_id} doesn't exist!")


@router.post("/users/logs/entrance", response_model=LogOutput, tags=["Log"], status_code=201)
async def submit_user_log_entrance(log: Log, user_id: uuid.UUID):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    user_shifts = target_user.shifts
    log_time = log.time
    given_log_date = log.log_date
    if given_log_date != date.today():
        raise HTTPException(status_code=422, detail="Date should be equal to the current day")
    if target_user.entry_logs[-1].time > target_user.exit_logs[-1].time:
        raise HTTPException(status_code=422, detail="Your last entry log doesn't have a matching exit log")
    pending_log = LogOutput(log_date=given_log_date, time=log_time, comment=log.comment, id=uuid.uuid4(), is_overtime=False, approved_overtime="00:00")
    for shift in user_shifts:
        days = list()
        if shift.type == "1":
            for day in shift.days:
                days.append(int(day.value))
        same_date_logs = []
        for exit_log in target_user.exit_logs:
            if exit_log.log_date == given_log_date and exit_log.time > shift.start:
                same_date_logs.append(exit_log)
        if len(same_date_logs) != 0:
            continue
        if given_log_date.today().weekday()+1 in days or shift.date == given_log_date:

            if timedelta(hours=log_time.hour, minutes=log_time.minute) < (timedelta(hours=shift.start.hour, minutes=shift.start.minute) - timedelta(hours=shift.flex_time.hour, minutes=shift.flex_time.minute)):
                pending_log.is_overtime = True
                target_user.entry_logs.append(pending_log)
                return pending_log
            elif timedelta(hours=log_time.hour, minutes=log_time.minute) > (timedelta(hours=shift.start.hour, minutes=shift.start.minute) + timedelta(hours=shift.permit_time.hour, minutes=shift.permit_time.minute)):
                raise HTTPException(status_code=409, detail="Permit time for entrance is over!")
            else:
                target_user.entry_logs.append(pending_log)
                return pending_log

    raise HTTPException(status_code=404, detail="There is no shift matching this log's date!")


@router.post("/users/logs/exit", response_model=LogOutput, tags=["Log"], status_code=201)
async def submit_user_log_exit(user_id: uuid.UUID, log: Log):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    user_shifts = target_user.shifts
    log_time = log.time
    given_log_date = log.log_date
    if given_log_date != date.today():
        raise HTTPException(status_code=422, detail="Date should be equal to the current day")
    if target_user.entry_logs[-1].time < target_user.exit_logs[-1].time:
        raise HTTPException(status_code=422, detail="Your last exit log doesn't have a matching entry log")
    pending_log = LogOutput(log_date=given_log_date, time=log_time, comment=log.comment, id=uuid.uuid4(), is_overtime=False, approved_overtime="00:00")
    for shift in user_shifts:
        days = list()
        if shift.type == "1":
            for day in shift.days:
                days.append(int(day.value))
        same_date_logs = []
        for exit_log in target_user.exit_logs:
            if exit_log.log_date == given_log_date and exit_log.time > shift.start:
                same_date_logs.append(exit_log)
        if len(same_date_logs) != 0:
            continue
        if given_log_date.today().weekday()+1 in days or shift.date == given_log_date:
            if timedelta(hours=log_time.hour, minutes=log_time.minute) > (
                    timedelta(hours=shift.end.hour, minutes=shift.end.minute) + timedelta(hours=shift.flex_time.hour,
                                                                                          minutes=shift.flex_time.minute)):
                pending_log.is_overtime = True
                target_user.exit_logs.append(pending_log)
                return pending_log
            else:
                target_user.exit_logs.append(pending_log)
                return pending_log

    raise HTTPException(status_code=404, detail="There is no shift matching this log's date!")


@router.put("/users/logs", response_model=LogOutput, tags=["Log"])
async def approve_user_log(user_id: uuid.UUID, log_id: uuid.UUID, date: date, time: time = Query(), comment: str | None = None, is_approved: bool = Query()):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    log = None
    for entry_log in target_user.entry_logs:
        if entry_log.id == log_id:
            log = entry_log

    for exit_log in target_user.exit_logs:
        if exit_log.id == log_id:
            log = exit_log
    if not log:
        raise HTTPException(status_code=404, detail=f"Log with id={log_id} doesn't exist!")
    log.is_approved = is_approved
    log.log_date = date
    log.time = time
    log.comment = comment
    return log


@router.patch("/users/logs", response_model=LogOutput, tags=["Log"])
def patch_user_log(user_id: uuid.UUID, log_id: uuid.UUID, date: date, time: time = Query(), comment: str | None = None, is_approved: bool = Query()):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    log = None
    for entry_log in target_user.entry_logs:
        if entry_log.id == log_id:
            log = entry_log

    for exit_log in target_user.exit_logs:
        if exit_log.id == log_id:
            log = exit_log
    if not log:
        raise HTTPException(status_code=404, detail=f"Log with id={log_id} doesn't exist!")
    log.is_approved = is_approved
    log.log_date = date
    log.time = time
    log.comment = comment
    return log


@router.get("/users/daily", response_model=bool, tags=["Calculate"])
async def calculate_daily_work(user_id: uuid.UUID, start: date, end: date):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    for holiday in holidays:
        if holiday.date == date:
            raise HTTPException(status_code=409, detail=f"Date {date} is a holiday!")
    user_entry_logs = []
    for log in target_user.entry_logs:
        if log.log_date >= start <= end:
            user_entry_logs.append(log)
    user_exit_logs = []
    for log in target_user.exit_logs:
        if log.log_date >= start <= end:
            user_exit_logs.append(log)

    if len(user_entry_logs) == 0 and len(user_exit_logs) == 0:
        return False
    else:
        return True


@router.get("/users/overtime", response_model=list[DailyWork], tags=["Calculate"])
def get_user_overtime(user_id: uuid.UUID, start: date, end: date, approval: bool):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    for holiday in holidays:
        if holiday.date == date:
            raise HTTPException(status_code=409, detail=f"Date {date} is a holiday!")
    user_entry_logs = []
    for log in target_user.entry_logs:
        if log.is_overtime and log.log_date >= start <= end:
            user_entry_logs.append(log)
    user_exit_logs = []
    for log in target_user.exit_logs:
        if log.is_overtime and log.log_date >= start <= end:
            user_exit_logs.append(log)

    if len(user_entry_logs) == len(user_exit_logs) == 0:
        raise HTTPException(status_code=404,
                            detail="User doesn't have any shift on this date or their log hasn't been approved!")

    if len(user_entry_logs) != len(user_exit_logs):
        raise HTTPException(status_code=422, detail="User's entry logs and exit logs are not equal")
    daily_work = []
    user_shifts = target_user.shifts
    for i in range(len(user_entry_logs)):
        if user_entry_logs[i].log_date == user_exit_logs[i].log_date:
            for shift in user_shifts:
                if user_entry_logs[i].time < shift.end and not user_exit_logs[i].time < shift.start:
                    days = list()
                    if shift.type == "1":
                        for day in shift.days:
                            days.append(int(day.value))
                    if user_entry_logs[i].log_date.today().weekday()+1 in days or shift.date == user_entry_logs[i].log_date:
                        hours = (timedelta(hours=user_exit_logs[i].time.hour, minutes=user_exit_logs[i].time.minute)
                                - timedelta(hours=user_entry_logs[i].time.hour, minutes=user_entry_logs[i].time.minute))
                        shift_hours = (timedelta(hours=shift.end.hour, minutes=shift.end.minute)
                                - timedelta(hours=shift.start.hour, minutes=shift.start.minute))
                        if hours > shift_hours:
                            if approval is False:
                                daily_work.append(DailyWork(date=user_entry_logs[i].log_date, hours=format_timespan(hours-shift_hours)))
                            else:
                                daily_work.append(DailyWork(date=user_entry_logs[i].log_date, hours=format_timespan(user_exit_logs)))

    return daily_work


@router.get("/users/undertime", response_model=list[DailyWork], tags=["Calculate"])
def get_user_undertime(user_id: uuid.UUID, start: date, end: date):
    target_user = None
    for user in users:
        if user_id == user.id:
            target_user = user
    if target_user is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    user_entry_logs = []
    for log in target_user.entry_logs:
        if log.log_date >= start <= end:
            user_entry_logs.append(log)
    user_exit_logs = []
    for log in target_user.exit_logs:
        if log.log_date >= start <= end:
            user_exit_logs.append(log)

    if len(user_entry_logs) == len(user_exit_logs) == 0:
        raise HTTPException(status_code=404,
                            detail="User doesn't have any shift on these dates or their log hasn't been approved!")

    if len(user_entry_logs) != len(user_exit_logs):
        raise HTTPException(status_code=422, detail="User's entry logs and exit logs are not equal")
    daily_work = []
    user_shifts = target_user.shifts
    for i in range(len(user_entry_logs)):
        if user_entry_logs[i].log_date == user_exit_logs[i].log_date:
            for shift in user_shifts:
                if user_entry_logs[i].time < shift.end and not user_exit_logs[i].time < shift.start:
                    days = list()
                    if shift.type == "1":
                        for day in shift.days:
                            days.append(int(day.value))
                    if user_entry_logs[i].log_date.today().weekday()+1 in days or shift.date == user_entry_logs[
                        i].log_date:
                        hours = (timedelta(hours=user_exit_logs[i].time.hour, minutes=user_exit_logs[i].time.minute)
                                 - timedelta(hours=user_entry_logs[i].time.hour,
                                             minutes=user_entry_logs[i].time.minute))
                        shift_hours = (timedelta(hours=shift.end.hour, minutes=shift.end.minute)
                                       - timedelta(hours=shift.start.hour, minutes=shift.start.minute))
                        if hours < shift_hours:
                            daily_work.append(DailyWork(date=user_entry_logs[i].log_date, hours=format_timespan(shift_hours-hours)))
    return daily_work


@router.post("/users", response_model=User, tags=["User"], status_code=201)
async def create_user(user: User):
    users.append(user)
    return user


@router.get("/users", response_model=list[User], tags=["User"])
async def get_users():
    return users
