import datetime


from humanfriendly import format_timespan
import uuid
from typing import List, Annotated
from sqlalchemy.orm import Session, defer
from sqlalchemy.sql import func
from app.db import SessionLocal, engine, get_db
from fastapi import APIRouter, Path, Query, Request, middleware, HTTPException, Body, Depends
from app.models import models
from fastapi.responses import RedirectResponse
from app.models.schemas import Shift, Type, Day, Holiday, Log, LogOutput, ShiftType1, ShiftType2, DailyWork, ShiftType1Output, ShiftType2Output, Event, EventOutput, UserShift
from datetime import date, time, timedelta
from ortools.sat.python import cp_model
from dateutil.rrule import rrule, DAILY
import pandas

models.Base.metadata.create_all(bind=engine)
router = APIRouter()


@router.post("/holidays", response_model=List[Holiday], tags=["Holidays"], status_code=201)
async def create_holidays(holiday_list: List[Holiday], db: Session = Depends(get_db)):
    for h in holiday_list:
        holiday = models.Holiday(date=h.date, name=h.name, created_by=uuid.uuid4())
        try:
            db.add(holiday)
            db.commit()
        except:
            raise HTTPException(status_code=409, detail=f"There is already a holiday on {h.date}")
        db.refresh(holiday)
    return holiday_list


@router.get("/holidays", response_model=list[Holiday], tags=["Holidays"])
async def get_holidays(start: date = Query(None, title="start date"), end: date = Query(None, title="end date"), specific_date: date = Query(None), db: Session = Depends(get_db)):
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        start = db.query(func.min(models.Holiday.date)).filter().scalar()
    if end is None:
        end = db.query(func.max(models.Holiday.date)).filter().scalar()
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start date!")
    holidays = db.query(models.Holiday).filter(models.Holiday.date >= start, models.Holiday.date <= end)
    return holidays


@router.delete("/holidays", tags=["Holidays"], status_code=204)
async def delete_holidays(date: date, db: Session = Depends(get_db)):

    holiday = db.query(models.Holiday).get(date)
    if not holiday:
        raise HTTPException(status_code=404, detail="There is no holiday on these dates!")
    db.delete(holiday)
    db.commit()
    return holiday


@router.put("/holidays", response_model=Holiday, tags=["Holidays"])
async def update_holiday(holiday_date: date, new_date: date = Query(None), new_name: str = Query(None), db: Session = Depends(get_db)):
    if not new_date and not new_name:
        raise HTTPException(status_code=400, detail="You most provide information!")
    target_holiday = db.query(models.Holiday).get(holiday_date)
    if not target_holiday:
        raise HTTPException(status_code=404, detail="There is no holiday on this date!")
    if new_name is not None:
        target_holiday.name = new_name
    if new_date is not None:
        target_holiday.date = new_date
    db.commit()
    return target_holiday


@router.patch("/holidays", response_model=Holiday, tags=["Holidays"])
async def update_holiday(holiday_date: date, new_date: date = Query(None), new_name: str = Query(None), db: Session = Depends(get_db)):
    if not new_date and not new_name:
        raise HTTPException(status_code=400, detail="You most provide information!")
    target_holiday = db.query(models.Holiday).get(holiday_date)
    if not target_holiday:
        raise HTTPException(status_code=404, detail="There is no holiday on this date!")
    if new_name is not None:
        target_holiday.name = new_name
    if new_date is not None:
        target_holiday.date = new_date
    db.commit()
    return target_holiday


@router.get("/workShifts", response_model=list[Shift], tags=["WorkShifts"])
async def get_shifts(db: Session = Depends(get_db)):
    return db.query(models.WorkShift).all()


@router.delete("/workShifts", tags=["WorkShifts"], status_code=204)
async def delete_shift(shift_id: uuid.UUID, db: Session = Depends(get_db)):
    shift = db.query(models.WorkShift).get(shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail=f"There is no shift with id={shift_id}")
    db.delete(shift)
    db.commit()
    return


@router.delete("/userShifts", tags=["UserShifts"], status_code=204)
async def delete_user_shift(user_id: uuid.UUID, shift_id: uuid.UUID, db: Session = Depends(get_db)):
   shift = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.shift_id == shift_id).first()
   if not shift:
       raise HTTPException(status_code=404, detail=f"There is no UserShift with shift_id={shift_id} and user_id={user_id}")
   db.delete(shift)
   db.commit()
   return


@router.patch("/workShifts/type1", response_model=Shift, tags=["WorkShifts"])
async def update_shift_type1(shift_id: uuid.UUID, start_time: time = Query(None), end_time: time = Query(None),  flex_time: time = Query(None), permit_time: time = Query(None),  days: List[Day] = Query(None), db: Session = Depends(get_db)):
    if all(info is None for info in (start_time, end_time, flex_time, permit_time, days)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    target_shift = db.query(models.WorkShift).get(shift_id)
    if target_shift is None:
        raise HTTPException(status_code=404, detail=f"Shift with id={shift_id} doesn't exist!")

    if target_shift.type == "2":
        raise HTTPException(status_code=409, detail="This shift is a type2 shift!")\

    if start_time is not None:
        target_shift.start_time = start_time
    if end_time is not None:
        target_shift.end_time = end_time
    if flex_time is not None:
        target_shift.flex_time = flex_time
    if permit_time is not None:
        target_shift.permit_time = permit_time
    if days is not None:
        target_shift.days = days
    db.commit()
    return target_shift


@router.patch("/workShifts/type2", response_model=Shift, tags=["WorkShifts"])
async def update_shift_type2(shift_id: uuid.UUID, start_time: time = Query(None),  end_time: time = Query(None),  flex_time: time = Query(None), permit_time: time = Query(None), date: date = Query(None), db: Session = Depends(get_db)):
    if all(info is None for info in (start_time, end_time, flex_time, permit_time, date)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    target_shift = db.query(models.WorkShift).get(shift_id)
    if not target_shift:
        raise HTTPException(status_code=404, detail=f"Shift with id={shift_id} doesn't exist!")
    if target_shift.type == "1":
        raise HTTPException(status_code=409, detail="This shift is a type1 shift!")

    if start_time is not None:
        target_shift.start_time = start_time
    if end_time is not None:
        target_shift.end_time = end_time
    if flex_time is not None:
        target_shift.flex_time = flex_time
    if permit_time is not None:
        target_shift.permit_time = permit_time
    if date is not None:
        target_shift.date = date
    db.commit()
    return target_shift


@router.get("/userShifts", response_model=list[Shift], tags=["UserShifts"])
def get_user_shifts(user_id: uuid.UUID, start: date = Query(None), end: date = Query(None), db: Session = Depends(get_db)):
    if start is None:
        start = date.min
    if end is None:
        end = date.max
    if start > end:
        raise HTTPException(status_code=422, detail="Start can't be after end")
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.activation >= start, models.UserShift.expiration <= end)
    output = []
    for user_shift in target_user_shifts:
        output.append(db.query(models.WorkShift).get(user_shift.shift_id))
    if target_user_shifts is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    return output


@router.post("/workShifts/type1", response_model=ShiftType1Output, tags=["WorkShifts"], status_code=201)
async def create_shift_type1(shift: ShiftType1, db: Session = Depends(get_db)):
    if shift.end < shift.start:
        raise HTTPException(status_code=422, detail="end time can't be before start time")
    id = uuid.uuid4()
    pending_shift = models.WorkShift(name=shift.name, days=shift.days, type=Type.one, start_time=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end_time=shift.end, date=None, id=id, created_by=uuid.uuid4())
    output_shift = ShiftType1Output(name=shift.name, days=shift.days, type=Type.one, start=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end=shift.end, id=id)
    db.add(pending_shift)
    db.commit()
    return output_shift


@router.post("/workShifts/type2", response_model=ShiftType2Output, tags=["WorkShifts"], status_code=201)
async def create_shift_type2(shift: ShiftType2, db: Session = Depends(get_db)):
    if shift.date < date.today():
        raise HTTPException(status_code=422, detail="Shift date can't be in the past")
    if shift.end < shift.start:
        raise HTTPException(status_code=422, detail="end time can't be before start time")
    id = uuid.uuid4()
    pending_shift = models.WorkShift(name=shift.name, days=None, type=Type.two, start_time=shift.start, flex_time=shift.flex_time,  permit_time=shift.permit_time, end_time=shift.end, date=shift.date, id=id, created_by=uuid.uuid4())
    output_shift = ShiftType2Output(name=shift.name, date=shift.date, type=Type.one, start=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end=shift.end, id=id)
    db.add(pending_shift)
    db.commit()
    return output_shift


@router.patch("/userShifts", response_model=UserShift, tags=["UserShifts"])
async def patch_user_shift(user_id: uuid.UUID, shift_id: uuid.UUID, is_expired: bool = Query(None), activation: date = Query(None), expiration: date = Query(None),  db: Session = Depends(get_db)):
    user_shift = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.shift_id == shift_id).first()
    if all(info is None for info in (is_expired, activation, expiration)):
        raise HTTPException(status_code=400, detail="No parameter provided for update")
    if is_expired is not None:
        user_shift.is_expired = is_expired
    if activation is not None:
        user_shift.activation = activation
    if expiration is not None:
        user_shift.expiration = expiration
    db.commit()
    return user_shift


@router.post("/userShifts", response_model=Shift, tags=["UserShifts"], status_code=201)
async def add_user_shift(user_id: uuid.UUID, shift_id: uuid.UUID, activation: date, expiration: date = Query(None), db: Session = Depends(get_db)):
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.is_expired == False)
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    if target_user_shifts is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    pending_shift = db.query(models.WorkShift).get(shift_id)
    pending_user_shift = models.UserShift(user_id=user_id, shift_id=shift_id, activation=activation, expiration=expiration, created_by=uuid.uuid4())
    if not pending_shift:
        raise HTTPException(status_code=404, detail=f"Shift with id={shift_id} doesn't exist!")
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    overlap_check = list()
    pending_shift_start = pending_shift.start_time.hour * 60 + pending_shift.start_time.minute
    pending_shift_end = pending_shift.end_time.hour * 60 + pending_shift.end_time.minute
    for shift in user_shifts:
        if shift.id == shift_id:
            raise HTTPException(status_code=409, detail="User has this shift already!")
        shift_start = shift.start_time.hour * 60 + shift.start_time.minute
        shift_end = shift.end_time.hour * 60 + shift.end_time.minute
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
                    days.append(int(day))
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
                    days.append(int(day))
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
                        deleted_user_shift = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.shift_id == shift.id).first()
                        db.delete(deleted_user_shift)
                        db.commit()
                        db.add(pending_user_shift)
                        db.commit()
                        return pending_shift

        model.AddNoOverlap(overlap_check)
        status = solver.Solve(model=model)
        if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
            raise HTTPException(status_code=409,
                                detail="Shift can't be scheduled because it is in conflict with another same type shift!")
    db.add(pending_user_shift)
    db.commit()
    return pending_shift


@router.post("/events", response_model=EventOutput, tags=["Events"], status_code=201)
async def create_event(event: Event, db: Session = Depends(get_db)):
    holiday = db.query(models.Holiday).get(event.date)
    if holiday:
        raise HTTPException(status_code=409, detail=f"{event.date} is a holiday!")
    if event.start > event.end:
        raise HTTPException(status_code=422, detail="End time can't be before start time.")
    id = uuid.uuid4()
    pending_event = models.Event(name=event.name, date=event.date, start=event.start, end=event.end, attendees=event.attendees, id=id, created_by=uuid.uuid4())
    db.add(pending_event)
    db.commit()
    for user_id in event.attendees:
        user_event = models.UserEvent(user_id=user_id, event_id=id)
        try:
            db.add(user_event)
            db.commit()
        except:
            raise HTTPException(status_code=409, detail="User has this event already!")
    return pending_event


@router.get("/users/events", response_model=list[EventOutput], tags=["Events"])
async def get_user_events(user_id: uuid.UUID, db: Session = Depends(get_db)):
    target_user_events = db.query(models.UserEvent).filter(models.UserEvent.user_id == user_id)
    output = []
    for user_event in target_user_events:
        output.append(db.query(models.Event).get(user_event.event_id))
    if target_user_events is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    return output


@router.get("/events", response_model=list[EventOutput], tags=["Events"])
async def get_events(db: Session = Depends(get_db)):
    return db.query(models.Event).all()


@router.delete("/events", tags=["Events"], status_code=204)
async def delete_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    event = db.query(models.Event).get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event with id={event_id} doesn't exist")
    db.delete(event)
    db.commit()


@router.patch("/events", response_model=EventOutput, tags=["Events"])
async def patch_event(event_id: uuid.UUID, attendees: list[uuid.UUID], date: date = Query(None), start: time = Query(None), end: time = Query(None), db: Session = Depends(get_db)):
    if all(info is None for info in (end, start, attendees, date)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    event = db.query(models.Event).get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event with id={event_id} doesn't exist")
    if date is not None:
        event.date = date
    if start is not None:
        event.start = start
    if end is not None:
        event.end = end
    if attendees is not None:
        event.attendees = attendees
    db.commit()
    return event


@router.get("/users/logs", response_model=list[LogOutput], tags=["Logs"])
async def get_user_logs(user_id: uuid.UUID, start: date = Query(None), end: date = Query(None), specific_date: date = Query(None), db: Session = Depends(get_db)):
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        start = date.min
    if end is None:
        end = date.max
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start day")
    if specific_date is not None:
        return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date == specific_date)
    else:
        return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date >= start, models.Log.date <= end)


@router.delete("/users/logs", tags=["Logs"], status_code=204)
async def delete_user_logs(log_id: uuid.UUID, db: Session = Depends(get_db)):
    log = db.query(models.Log).get(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"Log with id={log_id} doesn't exist!")
    db.delete(log)
    db.commit()
    return


@router.post("/users/logs/entrance", response_model=LogOutput, tags=["Logs"], status_code=201)
async def submit_user_log_entrance(log: Log, user_id: uuid.UUID, db: Session = Depends(get_db)):
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.is_expired == False)
    if not target_user_shifts:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist")
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    log_time = log.time
    given_log_date = log.date
    entry_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "entrance", models.Log.date == given_log_date))
    exit_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "exit", models.Log.date == given_log_date))
    if given_log_date != date.today():
        raise HTTPException(status_code=422, detail="Date should be equal to the current day")
    if len(entry_logs) > len(exit_logs):
        raise HTTPException(status_code=422, detail="Your last entry log doesn't have a matching exit log")
    id= uuid.uuid4()
    pending_log = models.Log(date=given_log_date, time=log_time, comment=log.comment, id=id, is_overtime=False, approved_overtime="00:00", type="entrance", user_id=user_id, created_by=uuid.uuid4())
    for shift in user_shifts:
        days = list()
        if shift.type == "1":
            for day in shift.days:
                days.append(int(day))
        same_date_logs = []
        for exit_log in exit_logs:
            if exit_log.date == given_log_date and exit_log.time > shift.start_time:
                same_date_logs.append(exit_log)
        if len(same_date_logs) != 0:
            continue
        if given_log_date.today().weekday()+1 in days or shift.date == given_log_date:

            if timedelta(hours=log_time.hour, minutes=log_time.minute) < (timedelta(hours=shift.start_time.hour, minutes=shift.start_time.minute) - timedelta(hours=shift.flex_time.hour, minutes=shift.flex_time.minute)):
                pending_log.is_overtime = True
                db.add(pending_log)
                db.commit()
                return pending_log
            elif timedelta(hours=log_time.hour, minutes=log_time.minute) > (timedelta(hours=shift.start_time.hour, minutes=shift.start_time.minute) + timedelta(hours=shift.permit_time.hour, minutes=shift.permit_time.minute)):
                raise HTTPException(status_code=409, detail="Permit time for entrance is over!")
            else:
                db.add(pending_log)
                db.commit()
                return pending_log

    raise HTTPException(status_code=404, detail="There is no shift matching this log's date!")


@router.get("/users/logs/entrance", response_model=list[LogOutput], tags=["Logs"])
async def get_user_entrance_logs(user_id: uuid.UUID, start: date = Query(None), end: date = Query(None), specific_date: date = Query(None), db: Session = Depends(get_db)):
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        start = date.min
    if end is None:
        end = date.max
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start day")
    if specific_date is None:
        return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "entrance", models.Log.date >= start, models.Log.date <= end)
    else:
        return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "entrance", models.Log.date == specific_date)


@router.get("/users/logs/exit", response_model=list[LogOutput], tags=["Logs"])
async def get_user_entrance_logs(user_id: uuid.UUID, start: date = Query(None), end: date = Query(None), specific_date: date = Query(None), db: Session = Depends(get_db)):
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        start = date.min
    if end is None:
        end = date.max
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start day")
    if specific_date is None:
        return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "exit", models.Log.date >= start, models.Log.date <= end)
    else:
        return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "exit", models.Log.date == specific_date)


@router.post("/users/logs/exit", response_model=LogOutput, tags=["Logs"], status_code=201)
async def submit_user_log_exit(user_id: uuid.UUID, log: Log, db: Session = Depends(get_db)):
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.is_expired == False)
    if not target_user_shifts:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist")
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    log_time = log.time
    given_log_date = log.date
    entry_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "entrance", models.Log.date == given_log_date))
    exit_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "exit", models.Log.date == given_log_date))
    if given_log_date != date.today():
        raise HTTPException(status_code=422, detail="Date should be equal to the current day")
    if len(entry_logs) < len(exit_logs):
        raise HTTPException(status_code=422, detail="Your last exit log doesn't have a matching entry log")
    id = uuid.uuid4()
    pending_log = models.Log(date=given_log_date, time=log_time, comment=log.comment, id=id, is_overtime=False, approved_overtime="00:00", type="exit", user_id=user_id, created_by=uuid.uuid4())
    for shift in user_shifts:
        days = list()
        if shift.type == "1":
            for day in shift.days:
                days.append(int(day))
        same_date_logs = []
        for exit_log in exit_logs:
            if exit_log.date == given_log_date and exit_log.time > shift.start_time:
                same_date_logs.append(exit_log)
        if len(same_date_logs) != 0:
            continue
        if given_log_date.today().weekday()+1 in days or shift.date == given_log_date:
            last_entry_log = db.query(func.max(models.Log.time)).filter(models.Log.user_id == user_id, models.Log.date == date.today(), models.Log.type == "entrance").scalar()
            if last_entry_log is None:
                last_entry_log = log_time
            if timedelta(hours=log_time.hour, minutes=log_time.minute) - timedelta(hours=last_entry_log.hour, minutes=last_entry_log.minute) > (
                    timedelta(hours=shift.end_time.hour, minutes=shift.end_time.minute) - timedelta(hours=shift.start_time.hour,
                                                                                          minutes=shift.start_time.minute)):
                pending_log.is_overtime = True
                db.add(pending_log)
                db.commit()
                return pending_log
            else:
                db.add(pending_log)
                db.commit()
                return pending_log

    raise HTTPException(status_code=404, detail="There is no shift matching this log's date!")


@router.put("/users/logs", response_model=LogOutput, tags=["Logs"])
async def approve_user_log(log_id: uuid.UUID, date: date = Query(None), time: time = Query(None), comment: str = Query(None), is_overtime: bool = Query(None), approved_overtime: time = Query(None), db: Session = Depends(get_db)):
    if all(info is None for info in (date, time, comment, is_overtime, approved_overtime)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    log = db.query(models.Log).get(log_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Log with id={log_id} doesn't exist")
    if date is not None:
        log.date = date
    if is_overtime is not None:
        log.is_overtime = is_overtime
    if time is not None:
        log.time = time
    if comment is not None:
        log.comment = comment
    if approved_overtime is not None:
        log.approved_overtime = approved_overtime
    db.commit()
    return log


@router.patch("/users/logs", response_model=LogOutput, tags=["Logs"])
def patch_user_log(log_id: uuid.UUID, date: date = Query(None), time: time = Query(None), comment: str = Query(None), is_overtime: bool = Query(None), approved_overtime: time = Query(None), db: Session = Depends(get_db)):
    if all(info is None for info in (date, time, comment, is_overtime, approved_overtime)):
        raise HTTPException(status_code=400, detail="No parameters provided for update")
    log = db.query(models.Log).get(log_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Log with id={log_id} doesn't exist")
    if date is not None:
        log.date = date
    if is_overtime is not None:
        log.is_overtime = is_overtime
    if time is not None:
        log.time = time
    if comment is not None:
        log.comment = comment
    if approved_overtime is not None:
        log.approved_overtime = approved_overtime
    db.commit()
    return log


@router.get("/users/logs/overtime", response_model=list[LogOutput], tags=["Logs"])
async def get_user_overtime_log(user_id: uuid.UUID = Query(None), start: date = Query(None), end: date = Query(None), approved_overtime: bool = Query(), specific_date: date = Query(None), db: Session = Depends(get_db)):
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        if user_id is not None:
            start = date.min
        else:
            start = db.query(func.min(models.Log.date)).filter().scalar()
    if end is None:
        if user_id is not None:
            end = date.max
        else:
            end = db.query(func.max(models.Log.date)).filter().scalar()
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start day")
    if user_id is None:
        if approved_overtime:
            return list(db.query(models.Log).filter(models.Log.date >= start, models.Log.date <= end, models.Log.approved_overtime != "00:00", models.Log.is_overtime == True))
        else:
            return list(db.query(models.Log).filter(models.Log.date >= start, models.Log.date <= end, models.Log.approved_overtime == "00:00", models.Log.is_overtime == True))
    else:
        if approved_overtime:
            return list(db.query(models.Log).filter(models.Log.date >= start, models.Log.date <= end, models.Log.approved_overtime != "00:00", models.Log.user_id == user_id, models.Log.is_overtime == True))
        else:
            return list(db.query(models.Log).filter(models.Log.date >= start, models.Log.date <= end, models.Log.approved_overtime == "00:00", models.Log.user_id == user_id, models.Log.is_overtime == True))


@router.get("/users/daily", response_model=list[DailyWork], tags=["Calculate"])
async def calculate_daily_work(user_id: uuid.UUID, start: date = Query(None), end: date = Query(None), specific_date: date = Query(None), db: Session = Depends(get_db)):
    logs = list(db.query(models.Log).filter(models.Log.user_id == user_id))
    if len(logs) == 0:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't have any logs")
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        start = db.query(func.min(models.Log.date)).filter(models.Log.user_id == user_id).scalar()
    if end is None:
        end = db.query(func.max(models.Log.date)).filter(models.Log.user_id == user_id).scalar()
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start day")
    daily_work_list = []
    for dt in rrule(DAILY, dtstart=start, until=end):
        dt = dt.strftime("%Y-%m-%d")
        log = db.query(models.Log).filter(models.Log.date == dt, models.Log.user_id == user_id).first()
        if log:
            daily_work_list.append(DailyWork(date=dt, hours="TRUE"))
        else:
            daily_work_list.append(DailyWork(date=dt, hours="FALSE"))
    return daily_work_list


@router.get("/users/overtime", response_model=list[DailyWork], tags=["Calculate"])
def get_user_overtime(user_id: uuid.UUID, start: date = Query(None), end: date = Query(None), approval: bool = Query(), specific_date: date = Query(None), db: Session = Depends(get_db)):
    logs = list(db.query(models.Log).filter(models.Log.user_id == user_id))
    if len(logs) == 0:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't have any logs")
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        start = db.query(func.min(models.Log.date)).filter(models.Log.user_id == user_id).scalar()
    if end is None:
        end = db.query(func.max(models.Log.date)).filter(models.Log.user_id == user_id).scalar()
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start day")
    user_entry_logs = list(
        db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date >= start,
                                    models.Log.type == "entrance", models.Log.date <= end))
    user_exit_logs = list(
        db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date >= start,
                                    models.Log.type == "exit", models.Log.date <= end))
    if len(user_entry_logs) == len(user_exit_logs) == 0:
        raise HTTPException(status_code=404,
                            detail="User doesn't have any shift on this date or their log hasn't been approved!")
    if len(user_entry_logs) != len(user_exit_logs):
        raise HTTPException(status_code=422, detail="User's entry logs and exit logs are not equal")
    daily_work = []
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id, models.UserShift.activation >= start, models.UserShift.expiration <= end)
    if not target_user_shifts:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist")
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    for i in range(len(user_entry_logs)):
        if user_entry_logs[i].date == user_exit_logs[i].date:
            for shift in user_shifts:
                shift_activation = db.query(models.UserShift.activation).filter(models.UserShift.user_id == user_id, models.UserShift.shift_id == shift.id).scalar()
                shift_expiration = db.query(models.UserShift.expiration).filter(models.UserShift.user_id == user_id, models.UserShift.shift_id == shift.id).scalar()
                if user_entry_logs[i].time < shift.end_time and not user_exit_logs[i].time < shift.start_time and user_entry_logs[i].date > shift_activation and user_entry_logs[i].date < shift_expiration:
                    days = list()
                    if shift.type == "1":
                        for day in shift.days:
                            days.append(int(day))
                    if user_entry_logs[i].date.today().weekday()+1 in days or shift.date == user_entry_logs[i].date:
                        hours = (timedelta(hours=user_exit_logs[i].time.hour, minutes=user_exit_logs[i].time.minute)
                                - timedelta(hours=user_entry_logs[i].time.hour, minutes=user_entry_logs[i].time.minute))
                        shift_hours = (timedelta(hours=shift.end_time.hour, minutes=shift.end_time.minute)
                                - timedelta(hours=shift.start_time.hour, minutes=shift.start_time.minute))
                        if hours > shift_hours:
                            if approval is False:
                                daily_work.append(DailyWork(date=user_entry_logs[i].date, hours=format_timespan(hours-shift_hours)))
                            else:
                                daily_work.append(DailyWork(date=user_entry_logs[i].date, hours=str(user_exit_logs[i].approved_overtime)))

    return daily_work


@router.get("/users/undertime", response_model=list[DailyWork], tags=["Calculate"])
def get_user_undertime(user_id: uuid.UUID, start: date = Query(None), end: date = Query(None), specific_date: date = Query(None), db: Session = Depends(get_db)):
    logs = list(db.query(models.Log).filter(models.Log.user_id == user_id))
    if len(logs) == 0:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't have any logs")
    if specific_date is not None:
        start = specific_date
        end = start
    if start is None:
        start = db.query(func.min(models.Log.date)).filter(models.Log.user_id == user_id).scalar()
    if end is None:
        end = db.query(func.max(models.Log.date)).filter(models.Log.user_id == user_id).scalar()
    if start > end:
        raise HTTPException(status_code=422, detail="End date can't be before start day")
    user_entry_logs = list(
        db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date >= start,
                                    models.Log.type == "entrance", models.Log.date <= end))
    user_exit_logs = list(
        db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date >= start,
                                    models.Log.type == "exit", models.Log.date <= end))
    if len(user_entry_logs) == len(user_exit_logs) == 0:
        raise HTTPException(status_code=404,
                            detail="User doesn't have any shift on this date or their log hasn't been approved!")
    if len(user_entry_logs) != len(user_exit_logs):
        raise HTTPException(status_code=422, detail="User's entry logs and exit logs are not equal")
    daily_work = []
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id)
    if not target_user_shifts:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist")
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    for i in range(len(user_entry_logs)):
        if user_entry_logs[i].date == user_exit_logs[i].date:
            for shift in user_shifts:
                shift_activation = db.query(models.UserShift.activation).filter(models.UserShift.user_id == user_id, models.UserShift.shift_id == shift.id).scalar()
                shift_expiration = db.query(models.UserShift.expiration).filter(models.UserShift.user_id == user_id, models.UserShift.shift_id == shift.id).scalar()
                if user_entry_logs[i].time < shift.end_time and not user_exit_logs[i].time < shift.start_time and user_entry_logs[i].date > shift_activation and user_entry_logs[i].date < shift_expiration:
                    days = list()
                    if shift.type == "1":
                        for day in shift.days:
                            days.append(int(day))
                    if user_entry_logs[i].date.today().weekday() + 1 in days or shift.date == user_entry_logs[i].date:
                        hours = (timedelta(hours=user_exit_logs[i].time.hour, minutes=user_exit_logs[i].time.minute)
                                 - timedelta(hours=user_entry_logs[i].time.hour,
                                             minutes=user_entry_logs[i].time.minute))
                        shift_hours = (timedelta(hours=shift.end_time.hour, minutes=shift.end_time.minute)
                                       - timedelta(hours=shift.start_time.hour, minutes=shift.start_time.minute))
                        if hours < shift_hours:
                                daily_work.append(
                                    DailyWork(date=user_entry_logs[i].date, hours=format_timespan(shift_hours - hours)))

    return daily_work



