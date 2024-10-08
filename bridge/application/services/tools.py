from datetime import datetime
from flask import session, Response
import json
from cryptography.fernet import Fernet
from functools import wraps
from typing import Dict, List, Union, Tuple
from application.configs.config import TRACK_TIME, FERNET_KEY
from application.services.error_handlers import CustomError


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


def get_member_training(training_id: int, member_trainings: List[Dict]) -> Union[Dict, None]:
    """
    Get training from trainings list by ID.
    :param training_id: ID of current failed training from Fabman DB
    :param member_trainings: list of courses
    :return: specific course from courses list, if it exists
    """

    return next((t for t in member_trainings if t["trainingCourse"] == training_id), None)


def get_current_training_with_index(failed_courses_list: List[Dict[str, str | int]], training_id: int
                                    ) -> Tuple[int, Dict] | None:
    """
    Find indexed training in training list.
    :param failed_courses_list: list of failed courses from users metadata
    :param training_id: ID of current failed training from Fabman DB
    :return: failed course in metadata and its index in failed_courses list if it exists
    """

    return next(((i, c) for i, c in enumerate(failed_courses_list) if c["id"] == training_id), None)


def decrypt_identifiers(crypto: str) -> str:
    """
    Decrypt user ID and training ID from Classmarker data.
    :param crypto: encrypted string '<user_id>-<training_id>'
    :return: '<user_id>-<training_id>'
    """

    identifiers = "-"

    if crypto:
        f = Fernet(FERNET_KEY.encode("ascii", "ignore"))
        identifiers = f.decrypt(crypto).decode()

    if not identifiers or len(identifiers.split("-")) != 2 or not identifiers.replace("-", "").isdigit():
        raise CustomError(f'Missing or wrong IDs: {identifiers} for {crypto}')

    return identifiers


def track_api_time(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        session.clear()
        start = datetime.now().timestamp()
        res = f(*args, **kwargs)
        stop = datetime.now().timestamp()
        session.setdefault("railway_processes_duration", round(stop - start - sum(session.values()), 3))
        session.setdefault("total", round(sum(session.values()), 3))

        headers = {"Content-Type": "application/json"}

        if TRACK_TIME:
            headers["Durations"] = dict(session)

        return (
            res if isinstance(res, Response) else json.dumps(res),
            200,
            headers
        )

    return decorator
