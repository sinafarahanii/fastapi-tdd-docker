import datetime

import sqlalchemy.exc
from humanfriendly import format_timespan
import uuid
from typing import List, Annotated
from sqlalchemy.orm import Session, defer
from app.db import SessionLocal, engine, get_db
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

shifts = [Shift(name="shift", type="1", start_time="09:00", end_time="18:00", flex_time="01:00", days=[Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY, Day.THURSDAY, Day.FRIDAY, Day.SATURDAY, Day.SUNDAY], id=uuid.uuid4(), date=None, permit_time="04:00"),
          Shift(name="shift", type="2", start_time="12:00", end_time="15:00", flex_time="00:30", days=None, id=uuid.uuid4(), date="2023-10-10", permit_time="04:00"),
          Shift(name="shift", type="2", start_time="13:00", end_time="16:00", flex_time="00:30", days=None, id=uuid.uuid4(), date="2023-10-10", permit_time="04:00"),
          Shift(name="shift", type="1", start_time="11:00", end_time="19:00", flex_time="01:00", days=[Day.MONDAY, Day.TUESDAY, Day.WEDNESDAY], id=uuid.uuid4(), date=None, permit_time="04:00")]


@router.post("/holidays", response_model=List[Holiday], tags=["Holidays"], status_code=201)
async def create_holidays(holiday_list: List[Annotated[Holiday, Body(examples=[{"name": "christmas", "date": "2024-01-01"}])]], db: Session = Depends(get_db)):
    holidays = db.query(models.Holiday).all()
    for h in holiday_list:
        holiday = models.Holiday(date=h.date, name=h.name)
        try:
            db.add(holiday)
            db.commit()
        except:
            raise HTTPException(status_code=409, detail=f"There is already a holiday on {h.date}")
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
def get_user_shifts(user_id: uuid.UUID, db: Session = Depends(get_db)):
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id)
    output = []
    for user_shift in target_user_shifts:
        output.append(db.query(models.WorkShift).get(user_shift.shift_id))
    if target_user_shifts is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    return output


@router.post("/workShifts/type1", response_model=ShiftType1Output, tags=["WorkShifts"], status_code=201)
async def create_shift_type1(
        shift: Annotated[
            ShiftType1,
            Body(
                examples=[
                    {
                        "name": "daily shift",
                        "start": "09:00",
                        "end": "18:00",
                        "flex_time": "01:00",
                        "permit_time": "04:00",
                        "days": [
                            "1",
                            "2",
                            "3",
                            "4",
                            "5"
                        ],
                    }
                ]
            )
        ], db: Session = Depends(get_db)):
    if shift.end < shift.start:
        raise HTTPException(status_code=422, detail="end time can't be before start time")
    id = uuid.uuid4()
    pending_shift = models.WorkShift(name=shift.name, days=shift.days, type=Type.one, start_time=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end_time=shift.end, date=None, id=id)
    output_shift = ShiftType1Output(name=shift.name, days=shift.days, type=Type.one, start=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end=shift.end, id=id)
    db.add(pending_shift)
    db.commit()
    return output_shift


@router.post("/workShifts/type2", response_model=ShiftType2Output, tags=["WorkShifts"], status_code=201)
async def create_shift_type2(
        shift: Annotated[
            ShiftType2,
            Body(
                examples=[
                    {
                        "name": "night shift",
                        "start": "19:00",
                        "end": "21:00",
                        "date": "2023-09-25",
                        "flex_time": "00:15",
                        "permit_time": "01:00",
                    }
                ]
            )
        ], db: Session = Depends(get_db)):
    if shift.date < date.today():
        raise HTTPException(status_code=422, detail="Shift date can't be in the past")
    if shift.end < shift.start:
        raise HTTPException(status_code=422, detail="end time can't be before start time")
    id = uuid.uuid4()
    pending_shift = models.WorkShift(name=shift.name, days=None, type=Type.two, start_time=shift.start, flex_time=shift.flex_time,  permit_time=shift.permit_time, end_time=shift.end, date=shift.date, id=id)
    output_shift = ShiftType2Output(name=shift.name, date=shift.date, type=Type.one, start=shift.start, flex_time=shift.flex_time, permit_time=shift.permit_time, end=shift.end, id=id)
    db.add(pending_shift)
    db.commit()
    return output_shift


@router.post("/userShifts", response_model=Shift, tags=["UserShifts"], status_code=201)
async def add_user_shift(user_id: uuid.UUID, shift_id: uuid.UUID, db: Session = Depends(get_db)):
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id)
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    if target_user_shifts is None:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist!")
    pending_shift = db.query(models.WorkShift).get(shift_id)
    pending_user_shift = models.UserShift(user_id=user_id, shift_id=shift_id)
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
                        deleted_user_shift = models.UserShift(user_id=user_id, shift_id=shift.id)
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
async def create_event(event: Annotated[
    Event,
    Body(
        examples=[
            {
                "name": "Anniversary meeting",
                "date": "2023-10-10",
                "start": "16:00",
                "end": "18:00",
                "attendees": [
                    "3fa85f64-5717-4562-b3fc-2c963f66afa6"
                ]
            }
        ]
    )], db: Session = Depends(get_db)):
    holiday = db.query(models.Holiday).get(event.date)
    if holiday:
        raise HTTPException(status_code=409, detail=f"{event.date} is a holiday!")
    if event.start > event.end:
        raise HTTPException(status_code=422, detail="End time can't be before start time.")
    id = uuid.uuid4()
    pending_event = models.Event(name=event.name, date=event.date, start=event.start, end=event.end, attendees=event.attendees, id=id)
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
async def get_user_logs(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(models.Log).filter(models.Log.user_id == user_id)


@router.delete("/users/logs", tags=["Logs"], status_code=204)
async def delete_user_logs(log_id: uuid.UUID, db: Session = Depends(get_db)):
    log = db.query(models.Log).get(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"Log with id={log_id} doesn't exist!")
    db.delete(log)
    db.commit()
    return


@router.post("/users/logs/entrance", response_model=LogOutput, tags=["Logs"], status_code=201)
async def submit_user_log_entrance(log: Annotated[
    Log,
    Body(
        examples=[
            {
                "date": str(date.today()),
                "time": "09:00",
                "comment": "i'm in"
            }
        ]
    )], user_id: uuid.UUID, db: Session = Depends(get_db)):
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id)
    if not target_user_shifts:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist")
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    log_time = log.time
    given_log_date = log.date
    entry_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "entrance", models.Log.date == date.today()))
    exit_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "exit", models.Log.date == date.today()))
    if given_log_date != date.today():
        raise HTTPException(status_code=422, detail="Date should be equal to the current day")
    if len(entry_logs) > len(exit_logs):
        raise HTTPException(status_code=422, detail="Your last entry log doesn't have a matching exit log")
    id= uuid.uuid4()
    pending_log = models.Log(date=given_log_date, time=log_time, comment=log.comment, id=id, is_overtime=False, approved_overtime="00:00", type="entrance", user_id=user_id)
    for shift in user_shifts:
        days = list()
        if shift.type == "1":
            for day in shift.days:
                days.append(int(day))
        same_date_logs = []
        for exit_log in exit_logs:
            if exit_log.log_date == given_log_date and exit_log.time > shift.start:
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
async def get_user_entrance_logs(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "entrance")


@router.get("/users/logs/exit", response_model=list[LogOutput], tags=["Logs"])
async def get_user_entrance_logs(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "exit")


@router.post("/users/logs/exit", response_model=LogOutput, tags=["Logs"], status_code=201)
async def submit_user_log_exit(user_id: uuid.UUID, log: Annotated[
    Log,
    Body(
        examples=[
            {
                "date": str(date.today()),
                "time": "18:00",
                "comment": "i'm out"
            }
        ]
    )], db: Session = Depends(get_db)):
    target_user_shifts = db.query(models.UserShift).filter(models.UserShift.user_id == user_id)
    if not target_user_shifts:
        raise HTTPException(status_code=404, detail=f"User with id={user_id} doesn't exist")
    user_shifts = []
    for user_shift in target_user_shifts:
        user_shifts.append(db.query(models.WorkShift).get(user_shift.shift_id))
    log_time = log.time
    given_log_date = log.date
    entry_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "entrance"))
    exit_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.type == "exit"))
    if given_log_date != date.today():
        raise HTTPException(status_code=422, detail="Date should be equal to the current day")
    if len(entry_logs) < len(exit_logs):
        raise HTTPException(status_code=422, detail="Your last exit log doesn't have a matching entry log")
    id = uuid.uuid4()
    pending_log = models.Log(date=given_log_date, time=log_time, comment=log.comment, id=id, is_overtime=False, approved_overtime="00:00", type="exit", user_id=user_id)
    for shift in user_shifts:
        days = list()
        if shift.type == "1":
            for day in shift.days:
                days.append(int(day))
        same_date_logs = []
        for exit_log in exit_logs:
            if exit_log.log_date == given_log_date and exit_log.time > shift.start:
                same_date_logs.append(exit_log)
        if len(same_date_logs) != 0:
            continue
        if given_log_date.today().weekday()+1 in days or shift.date == given_log_date:
            if timedelta(hours=log_time.hour, minutes=log_time.minute) > (
                    timedelta(hours=shift.end_time.hour, minutes=shift.end_time.minute) + timedelta(hours=shift.flex_time.hour,
                                                                                          minutes=shift.flex_time.minute)):
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


@router.get("/users/daily", response_model=bool, tags=["Calculate"])
async def calculate_daily_work(user_id: uuid.UUID, date: date, db: Session = Depends(get_db)):
    holiday = db.query(models.Holiday).get(date)
    if holiday:
        raise HTTPException(status_code=409, detail=f"Date {date} is a holiday!")
    user_entry_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date == date, models.Log.type == "entrance"))
    user_exit_logs = list(db.query(models.Log).filter(models.Log.user_id == user_id, models.Log.date == date, models.Log.type == "exit"))
    if len(user_entry_logs) == 0 and len(user_exit_logs) == 0:
        return False
    else:
        return True


@router.get("/users/overtime", response_model=list[DailyWork], tags=["Calculate"])
def get_user_overtime(user_id: uuid.UUID, start: date, end: date, approval: bool, db: Session = Depends(get_db)):
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
                if user_entry_logs[i].time < shift.end_time and not user_exit_logs[i].time < shift.start_time:
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
def get_user_undertime(user_id: uuid.UUID, start: date, end: date, db: Session = Depends(get_db)):
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
                if user_entry_logs[i].time < shift.end_time and not user_exit_logs[i].time < shift.start_time:
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
                                    DailyWork(date=user_entry_logs[i].date, hours=format_timespan(hours - shift_hours)))

    return daily_work



