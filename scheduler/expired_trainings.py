from functions import *


@error_handler
def check_expired_trainings():
    """
    Check all trainings of all members. Send email notification and remove training if it's expired.
    """
    if os.getenv("TEST_USER"):
        members = [data_from_get_request(
            f'https://fabman.io/api/v1/members/{os.getenv("TEST_USER")}?embed=trainings',
            os.getenv("FABMAN_API_KEY")
        )]

    else:
        members = data_from_get_request("https://fabman.io/api/v1/members?embed=trainings", os.getenv("FABMAN_API_KEY"))

    checked_trainings = 0
    expired_trainings = 0

    for m in members:
        for t in m["_embedded"]["trainings"]:
            checked_trainings += 1

            if not (expired_date(t["untilDate"]) if t.get("untilDate") else False):
                print(f'training {t["trainingCourse"]} is not expired for user {m["id"]}')
                continue

            expired_trainings += 1

            if send_expiration_notification(m["id"], t["trainingCourse"]):
                remove_expired_course(m["id"], t["id"])

    print(f'Checked {checked_trainings} trainings of {len(members)} members. Expired {expired_trainings} trainings.')
