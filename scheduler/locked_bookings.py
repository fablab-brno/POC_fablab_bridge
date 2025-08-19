from functions import *
from datetime import datetime, timedelta
from copy import deepcopy


@error_handler
def check_locked_bookings():
    """
    Check all trainings of all members. Send email notification and remove training if it's expired.
    """
    if os.getenv("TEST_USER"):
        members = [data_from_get_request(
            f'https://fabman.io/api/v1/members/{os.getenv("TEST_USER")}',
            FABMAN_API_KEY
        )]

    else:
        members = data_from_get_request("https://fabman.io/api/v1/members", FABMAN_API_KEY)

    now = datetime.now()
    check_end_datetime = now + timedelta(days=int(os.getenv("LOCKED_BOOKINGS_CHECK_DAYS_BEFORE",)))
    mail_sent = 0

    locked_resources = data_from_get_request(f'https://fabman.io/api/v1/resources?state=locked', FABMAN_API_KEY)

    bookings = data_from_get_request(
        f'https://fabman.io/api/v1/bookings?state=confirmed&fromDateTime={now.strftime("%Y-%m-%dT%H:%m")}&untilDateTime={check_end_datetime.strftime("%Y-%m-%dT%H:%m")}',
        FABMAN_API_KEY
    )

    for m in members:
        metadata = m["metadata"] or {"booking_notifications": []}
        lock_version = m["lockVersion"]

        if not metadata.get("booking_notifications"):
            metadata["booking_notifications"] = []

        checked_bookings = metadata.get("booking_notifications")

        for b in [bk for bk in bookings if bk["member"] == m["id"]]:
            if b["id"] in checked_bookings:
                print(f'{b["id"]} notification skip - already sent')
                continue

            locked_booked_resource = next((r for r in locked_resources if r["id"] == b["resource"]), None)

            if locked_booked_resource:
                if not send_locked_booking(m["id"], m["emailAddress"], locked_booked_resource["name"]):
                    print(f'Error during booking {b["id"]} notification for member {m["id"]}')
                    continue

                new_metadata = deepcopy(metadata)
                new_metadata["booking_notifications"].append(b["id"])
                metadata, lock_version = update_member_locked_booking(new_metadata, m["id"], lock_version)

                mail_sent += 1

    print(f'SUCCESS! {mail_sent} emails sent')


@error_handler
def reset_locked_bookings():
    if os.getenv("TEST_USER"):
        members = [data_from_get_request(
            f'https://fabman.io/api/v1/members/{os.getenv("TEST_USER")}',
            os.getenv("FABMAN_API_KEY")
        )]

    else:
        members = data_from_get_request("https://fabman.io/api/v1/members", os.getenv("FABMAN_API_KEY"))

    resets = 0

    for m in members:
        metadata = m["metadata"] or {"booking_notifications": []}

        if not metadata["booking_notifications"]:
            continue

        lock_version = m["lockVersion"]
        metadata["booking_notifications"] = []

        new_metadata = deepcopy(metadata)
        new_metadata["booking_notifications"] = []
        update_member_locked_booking(new_metadata, m["id"], lock_version)

        resets += 1

    print(f'SUCCESS! {resets} resets total')

