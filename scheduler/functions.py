import os
import requests
from datetime import datetime
from typing import List, Dict, Union
import traceback
from functools import wraps


RAILWAY_API_URL = os.getenv("RAILWAY_API_URL")
CRONJOB_TOKEN = os.getenv("CRONJOB_TOKEN")
FABMAN_API_KEY = os.getenv("FABMAN_API_KEY")


class CustomError(Exception):
    def __init__(self, description, error_data=None):
        self.args = (description, error_data)
        self.description = description
        self.data = error_data
        super().__init__()

    def __str__(self):
        return self.description


def expired_date(dt: str, date: bool = True) -> bool:
    """
    Compare specific date/datetime with current date/datetime and return if provided date is expired.
    :param dt: ISO string date ('2023-9-28')
    :param date: True if function should compare dates, False for comparing datetimes
    :return: bool - provided date is expired
    """
    dt = datetime(*[int(i) for i in dt.split("-")])

    if date:
        return dt.date() < datetime.now().date()

    return dt < datetime.now()


def data_from_get_request(url: str, token: str) -> Union[List, Dict]:
    """
    Function for GET requests with auth header, returning fetched data.
    :param url: API URL
    :param token: Fabman API token with admin permissions
    :raises Error during data fetching: request failed
    :return: data from GET request
    """
    res = requests.get(url, headers={"Authorization": f'{token}'})

    if res.status_code != 200:
        raise CustomError("Error during data fetching", f'{url}, {res.json()}')

    return res.json()


def send_expiration_notification(member_id: int, training_course_id: int) -> bool:
    res = requests.post(
        f'{RAILWAY_API_URL}/training_expiration',
        json={
            "member_id": member_id,
            "training_id": training_course_id
        },
        headers={"CronjobToken": f'{CRONJOB_TOKEN}'}
    )

    if res.status_code != 200:
        print(f'Error during {training_course_id} for user {member_id}')
        print(res.content)

    else:
        print(f'email with training {training_course_id} sent to user {member_id}')

    return res.status_code == 200


def send_locked_booking(member_id: int, member_email: str, resource: str):
    res = requests.post(
        f'{RAILWAY_API_URL}/locked-booking',
        json={
            "member_id": member_id,
            "member_email": member_email,
            "resource": resource
        },
        headers={"CronjobToken": f'{CRONJOB_TOKEN}'}
    )

    if res.status_code != 200:
        print(f'Error during bookings check for user {member_id}')
        print(res.content)

    else:
        print(f'Bookings of {member_id} successfully checked')

    return res.status_code == 200


def remove_expired_course(member_id: int, user_course_id: int) -> bool:
    res = requests.delete(
        f'https://fabman.io/api/v1/members/{member_id}/trainings/{user_course_id}',
        headers={"Authorization": f'{FABMAN_API_KEY}'}
    )

    if res.status_code != 204:
        print(f'Error during removing {user_course_id} for user {member_id}')
        print(res.content)

    else:
        print(f'Training {user_course_id} removed from user {member_id}')

    return res.status_code == 200


def railway_api_healtcheck() -> bool:
    res = requests.get(f'{RAILWAY_API_URL}/health', headers={"CronjobToken": f'{CRONJOB_TOKEN}'})

    if res.status_code != 200:
        print("Railway API is probably down")

    return res.status_code == 200


def update_member_locked_booking(metadata: dict, member_id: int, lock_version: int):
    new_member_data = {
        "lockVersion": lock_version,
        "metadata": metadata
    }

    res = requests.put(
        f'https://fabman.io/api/v1/members/{member_id}',
        json=new_member_data,
        headers={"Authorization": f'{FABMAN_API_KEY}'}
    )

    if res.status_code != 200:
        raise CustomError("Error during updating locked bookings")

    return res.json()["metadata"], lock_version + 1


def error_handler(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        try:
            return f(*args, **kwargs)

        except Exception:
            print(traceback.format_exc())

    return decorator
