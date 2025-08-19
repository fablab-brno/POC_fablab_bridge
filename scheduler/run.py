import os
import requests

from expired_trainings import check_expired_trainings
from locked_bookings import check_locked_bookings, reset_locked_bookings
from functions import RAILWAY_API_URL


def run_scheduled_task():
    if requests.get(f'{RAILWAY_API_URL}/health').status_code != 200:
        print(f'no healthcheck on {RAILWAY_API_URL}/health')
        return

    task = os.getenv("SCHEDULED_TASK")
    print(f'RUN TASK: {task.upper()}')

    if task == "locked_bookings":
        check_locked_bookings()

    elif task == "reset_locked_bookings":
        reset_locked_bookings()

    elif task == "expired_trainings":
        check_expired_trainings()

    else:
        print(f'UNKNOWN TASK {task}')


if __name__ == "__main__":
    run_scheduled_task()
