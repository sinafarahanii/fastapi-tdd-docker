import datetime
import json
import uuid


from app.main import app
from tests.test_main import test_app
from datetime import time, date, datetime
import pytest


"""""
 /holidays
"""""


"""""
Testing POST /holidays correctly
"""""
def test_create_holidays(test_app):
    payload = [{
        "name": "christmas",
        "date": str(date.today())
    },
        {
            "name": "eid",
            "date": "2024-01-01"
        }
    ]
    response = test_app.post("/holidays/", json=payload)
    assert response.status_code == 201, response.json()
    print(response.json())


"""""
Testing POST /holidays with repetitive date
"""""
def test_create_holidays_repetitive_date(test_app):
    payload = [{
        "name": "christmas",
        "date": str(date.today())
    }]
    response = test_app.post("/holidays/", json=payload)
    assert response.status_code == 409, response.json()
    assert response.json() == {"detail": f"There is already a holiday on {date.today()}"}


"""""
Testing GET /holidays correctly
"""""
def test_get_holidays(test_app):
    response = test_app.get("/holidays/", params={"start": "2023-01-01", "end": "2024-01-01"})
    assert response.status_code == 200, response.json()
    print(response.json())


"""""
Testing GET /holidays with given wrong dates
"""""
def test_get_holidays_wrong_dates(test_app):
    response = test_app.get("/holidays/", params={"start": "2024-01-01", "end": "2023-01-01"})
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == "End date can't be before start date!"

"""""
Testing DELETE /holidays correctly
"""""
def test_delete_holidays(test_app):

    response = test_app.delete("http://127.0.0.1:8000/holidays/", params={"date": str(date.today())})
    assert response.status_code == 204, response.json()

"""""
Testing PATCH /holidays correctly
"""""
def test_update_holiday(test_app):
    payload = {
        "holiday_date": "2024-01-01",
        "new_name": "Christmas"
    }
    response = test_app.patch("/holidays", params=payload)
    assert response.status_code == 200, response.json()
    print(response.json())


"""""
    /workShifts
"""""

"""""
Testing GET /workShifts correctly
"""""
def test_get_shifts(test_app):
    payload = {
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
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    response = test_app.get("/workShifts")
    assert response.status_code == 200, response.json()
    print(response.json())

"""""
Testing DELETE /workShifts correctly
"""""
def test_delete_shifts(test_app):
    payload = {
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
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id = response.json()["id"]
    response = test_app.delete("/workShifts", params={"shift_id": shift_id})
    assert response.status_code == 204, response.json()


"""""
    /workShifts/type2
"""""

"""""
Testing POST /workShifts/type2 correctly
"""""
def test_create_shift_type2_correctly(test_app):
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "date": str(date.today()),
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 201, response.json()
    print(response.json())

"""""
Testing POST /workShifts/type2 with start time later than end time
"""""
def test_create_shift_type2_start_later_than_end(test_app):
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "08:00",
        "flex_time": "01:00",
        "date": str(date.today()),
        "permit_time": "04:00"
    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == "end time can't be before start time"

"""""
Testing POST /workShifts/type2 with date earlier than current date
"""""
def test_create_shift_type2_date_earlier_than_current_date(test_app):
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "08:00",
        "flex_time": "01:00",
        "date": "2023-09-01",
        "permit_time": "04:00"
    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == "Shift date can't be in the past"

"""""
Testing PATCH /workShifts/type2 correctly
"""""
def test_update_shift_type2(test_app):
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "date": "2024-09-03",
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    shift_id = response.json()["id"]
    assert response.status_code == 201, response.json()
    response = test_app.patch("/workShifts/type2", params={"shift_id": shift_id, "date": str(date.today())})
    assert response.status_code == 200, response.json()


"""""
    /workShifts/type1
"""""

"""""
Testing POST /workShifts/type1 correctly
"""""
def test_create_shift_type1(test_app):
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    print(response.json())

"""""
Testing POST /workShifts/type1 with missing input field
"""""
def test_create_shift_type1_missing_input(test_app):
    payload = {
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": [1, 2, 3, 4, 5, 6, 7]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 422, response.json()

"""""
Testing PATCH /workShifts/type1 correctly
"""""
def test_update_shift_type1(test_app):
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id = response.json()["id"]
    response = test_app.patch("/workShifts/type1", params={"shift_id": shift_id, "permit_time": "03:00"})
    assert response.status_code == 200, response.json()


"""""
    /userShifts
"""""

"""""
Testing GET /userShifts correctly
"""""
def test_get_user_shifts(test_app):
    response = test_app.get("/userShifts", params={"user_id": uuid.uuid4()})
    assert response.status_code == 200, response.json()
    print(response.json())

"""""
Testing POST /userShifts correctly
"""""
def test_add_user_shift(test_app):
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": uuid.uuid4(), "shift_id": shift_id, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    print(response.json())

"""""
Testing POST /userShifts with invalid shift id
"""""
def test_add_user_shift_invalid_shift_id(test_app):
    shift_id = uuid.uuid4()
    response = test_app.post("/userShifts", params={"user_id": uuid.uuid4(), "shift_id": shift_id, "activation": str(date.today())})
    assert response.status_code == 404, response.json()
    assert response.json()["detail"] == f"Shift with id={shift_id} doesn't exist!"

"""""
Testing POST /userShifts with shift type2 overlapping shift type1 (not allowed)
"""""
def test_add_user_shift_overlap_shift_type2_with_shift_type1(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "date": "2024-09-03",
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type2 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type2, "activation": str(date.today())})
    assert response.status_code == 409, response.json()
    assert response.json()["detail"] == "Shift can't be scheduled because it is in conflict with another type 1 shift!"

"""""
Testing POST /userShifts with shift type1 overlapping shift type2 (shift type2 will be replaced)
"""""
def test_add_user_shift_overlap_shift_type1_with_shift_type2(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "date": "2024-09-03",
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type2 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type2, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()

"""""
Testing POST /userShifts with shift type1 overlapping shift type1 (not allowed)
"""""
def test_add_user_shift_overlap_shift_type1_with_shift_type1(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "name": "type1 shift",
        "start": "11:00",
        "end": "19:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 409, response.json()
    assert response.json()["detail"] == "Shift can't be scheduled because it is in conflict with another same type shift!"

"""""
Testing POST /userShifts with shift type2 overlapping shift type2
"""""
def test_add_user_shift_overlap_shift_type2_with_shift_type2(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "date": "2024-09-03",
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type2 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type2, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "name": "type2 shift",
        "start": "15:00",
        "end": "19:00",
        "flex_time": "01:00",
        "date": "2024-09-03",
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type2 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type2, "activation": str(date.today())})
    assert response.status_code == 409, response.json()
    assert response.json()["detail"] == "Shift can't be scheduled because it is in conflict with another same type shift!"

"""""
Testing DELETE /userShifts correctly
"""""
def test_delete_user_shift(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "date": "2024-09-03",
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type2 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type2, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    response = test_app.delete("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type2, "activation": str(date.today())})
    assert response.status_code == 204, response.json()

"""""
Testing PATCH /userShifts correctly
"""""
def test_patch_user_shift(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type2 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "date": "2024-09-03",
        "permit_time": "04:00"

    }
    response = test_app.post("/workShifts/type2", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type2 = response.json()["id"]
    response = test_app.post("/userShifts",
                             params={"user_id": user_id, "shift_id": shift_id_type2, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    response = test_app.patch("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type2, "is_expired": True})
    assert response.status_code == 200, response.json()
    print(response.json())


"""""
    /users/logs/entrance
"""""

"""""
Testing POST /users/logs/entrance correctly
"""""
def test_submit_user_log_entrance(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "08:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    print(response.json())

"""""
Testing POST /users/logs/entrance with invalid date
"""""
def test_submit_user_log_entrance_invalid_date(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": "2022-01-01",
        "time": "09:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == "Date should be equal to the current day"

"""""
Testing POST /users/logs/entrance with repetitive entrance logs
"""""
def test_submit_user_log_entrance_consecutive_entrance_log(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "09:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "10:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == "Your last entry log doesn't have a matching exit log"


"""""
    /users/logs/exit
"""""

"""""
Testing POST /users/logs/exit correctly
"""""
def test_submit_user_log_exit(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "17:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/exit", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    print(response.json())

"""""
Testing POST /users/logs/exit invalid date
"""""
def test_submit_user_log_exit_invalid_date(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": "2022-01-01",
        "time": "09:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == "Date should be equal to the current day"

"""""
Testing POST /users/logs/exit with repetitive exit logs
"""""
def test_submit_user_log_exit_consecutive_exit_log(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "17:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/exit", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "18:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/exit", params={"user_id": user_id}, json=payload)
    assert response.status_code == 422, response.json()
    assert response.json()["detail"] == "Your last exit log doesn't have a matching entry log"


"""""
    /users/logs
"""""


"""""
Testing GET /users/logs correctly
"""""
def test_get_user_logs(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "08:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    response = test_app.get("/users/logs", params={"user_id": user_id})
    assert response.status_code == 200, response.json()
    print(response.json())

"""""
Testing DELETE /users/logs correctly
"""""
def test_delete_user_logs(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "08:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    log_id = response.json()["id"]
    assert response.status_code == 201, response.json()
    response = test_app.delete("/users/logs", params={"user_id": user_id, "log_id": log_id})
    assert response.status_code == 204, response.json()

"""""
Testing PATCH /users/logs correctly
"""""
def test_patch_user_log(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "08:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    log_id = response.json()["id"]
    assert response.status_code == 201, response.json()
    response = test_app.patch("/users/logs", params={"log_id": log_id, "time": "09:00"})
    assert response.status_code == 200, response.json()
    print(response.json())


"""""
    /users/overtime
"""""

"""""
Testing GET /users/overtime correctly
"""""
def test_get_user_overtime(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "08:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "18:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/exit", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    response = test_app.get("/users/overtime", params={"user_id": user_id, "start": "2023-09-01", "end": "2029-10-01", "approval": False})
    assert response.status_code == 200, response.json()
    print(response.json())


"""""
    /users/undertime
"""""


"""""
Testing GET /users/undertime correctly
"""""
def test_get_user_undertime(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "09:30",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "18:00",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/exit", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    response = test_app.get("/users/undertime", params={"user_id": user_id, "start": "2023-09-01", "end": "2023-10-01"})
    assert response.status_code == 200, response.json()
    print(response.json())


"""""
    /users/daily
"""""

"""""
Testing GET /users/daily correctly
"""""
def test_calculate_daily_work(test_app):
    user_id = uuid.uuid4()
    payload = {
        "name": "type1 shift",
        "start": "09:00",
        "end": "18:00",
        "flex_time": "01:00",
        "permit_time": "04:00",
        "days": ["1", "2", "3", "4", "5", "6", "7"]
    }
    response = test_app.post("/workShifts/type1", json=payload)
    assert response.status_code == 201, response.json()
    shift_id_type1 = response.json()["id"]
    response = test_app.post("/userShifts", params={"user_id": user_id, "shift_id": shift_id_type1, "activation": str(date.today())})
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "09:00",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/entrance", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    payload = {
        "date": str(date.today()),
        "time": "18:00",
        "comment": "Are you telling me that a shrimp fried this rice?"
    }
    response = test_app.post("/users/logs/exit", params={"user_id": user_id}, json=payload)
    assert response.status_code == 201, response.json()
    response = test_app.get("/users/daily", params={"user_id": user_id, "date": str(date.today())})
    assert response.status_code == 200, response.json()
    print(response.json())


if __name__ == "__main__":
    pytest.main([__file__])
