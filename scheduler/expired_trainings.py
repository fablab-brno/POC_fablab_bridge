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
        members = []
        should_continue = True
        count = 500
        page = 0

        while should_continue:
            res = data_from_get_request(f'https://fabman.io/api/v1/members?embed=trainings&limit={count}&offset={count * page}', os.getenv("FABMAN_API_KEY"))
            should_continue = len(res) > 0
            page += 1
            members.extend(res)

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


def get_packages():
    packages = []

    members = []
    should_continue = True
    count = 500
    page = 0

    while should_continue:
        res = data_from_get_request(
            f'https://fabman.io/api/v1/members?embed=memberPackages&limit={count}&offset={count * page}',
            os.getenv("FABMAN_API_KEY"))
        should_continue = len(res) > 0
        page += 1
        members.extend(res)

    print(f'Fetched {len(members)} members')
    members_without_membership = 0
    members_with_membership = 0

    total_memberships = 0

    for m in members:
        row = {
            "member_id": m["id"],
            "gender": m["gender"],
            "member_createdAt": m["createdAt"],
            "id": "-",
            "package_name": "-",
            "package_id": "-",
            "from_date": "-",
            "until_date": "-"
        }

        if not m["_embedded"].get("memberPackages") or len(m["_embedded"]["memberPackages"]) == 0:
            members_without_membership += 1
            packages.append(row)
            continue

        members_with_membership += 1

        for t in m["_embedded"]["memberPackages"]:
            row["id"] = t["id"]
            row["package_id"] = t["package"]
            row["package_name"] = t["_embedded"]["package"]["name"]
            row["from_date"] = t["fromDate"]
            row["until_date"] = t["untilDate"]

            total_memberships += 1

            packages.append(row)

    print(f'Fetched {total_memberships} memberships. {members_without_membership} members without membership, {members_with_membership} with membership.')
    pass

    import json
    from pathlib import Path

    with open(Path(os.getcwd()) / "memberships_table.csv", "w") as csv:
        csv.write(";".join(packages[0].keys()) + "\n")

        for p in packages:
            csv.write(";".join([str(v) for v in p.values()]) + "\n")

    with open(Path(os.getcwd()) / "memberships_list.json", "w") as js:
        json.dump(packages, js, indent=4)

    with open(Path(os.getcwd()) / "members_with_memberships.json", "w") as mjs:
        mwm = [
            {
                "member_id": m["id"],
                "gender": m["gender"],
                "packages": [
                    {
                        "id": p["id"],
                        "package_id": p["package_id"],
                        "package_name": p["package_name"],
                        "from_date": p["from_date"],
                        "until_date": p["until_date"]
                    }
                    for p in packages
                    if p["member_id"] == m["id"]
                       and p["from_date"] != "-"
                ]
            } for m in members
        ]

        json.dump(mwm, mjs, indent=4)


get_packages()