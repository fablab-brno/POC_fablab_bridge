import os
import requests
import traceback
from datetime import datetime

from ..configs.config import FABMAN_API_KEY


# Ad-hoc latency benchmark. Set BRIDGE_BASE_URL and LOAD_TEST_MEMBER_ID before running.
BRIDGE_BASE_URL = os.getenv("BRIDGE_BASE_URL", "http://localhost:8000")
MEMBER_ID = os.getenv("LOAD_TEST_MEMBER_ID", "")

failed = 0
log_path = os.path.join(os.getcwd(), "log.csv")

if os.path.exists(log_path):
    os.remove(log_path)

with open(log_path, "w") as log_file:
    log_file.write("ID;ABSOLVED_PROCESSING;AVAILABLE_PROCESSING\n")

for i in range(20):
    try:
        start_absolved = datetime.now().timestamp()
        requests.get(f"{BRIDGE_BASE_URL}/absolved_trainings/{MEMBER_ID}", headers={"Authorization": FABMAN_API_KEY})
        stop_absolved = datetime.now().timestamp()

        start_available = datetime.now().timestamp()
        requests.get(f"{BRIDGE_BASE_URL}/available_trainings/{MEMBER_ID}", headers={"Authorization": FABMAN_API_KEY})
        stop_available = datetime.now().timestamp()

        absolved_duration = round(stop_absolved - start_absolved, 2)
        available_duration = round(stop_available - start_available, 2)

        with open(log_path, "a") as log:
            log.write(f'{i + 1};{absolved_duration};{available_duration}\n')

        print(i + 1, absolved_duration, available_duration)

    except Exception as e:
        failed += 1
        print(traceback.format_exc())
