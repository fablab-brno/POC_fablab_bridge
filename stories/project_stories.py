import os
import requests
import traceback
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import List, Dict, Union
from zoneinfo import ZoneInfo

from machines import machine_phrase, NEVER_ASK


FABMAN_API_URL = os.getenv("FABMAN_API_URL", "https://fabman.io/api/v1")
FABMAN_API_KEY = os.getenv("FABMAN_API_KEY")
RAILWAY_API_URL = os.getenv("RAILWAY_API_URL")
CRONJOB_TOKEN = os.getenv("CRONJOB_TOKEN")


def env_ids(name: str) -> List[int]:
    return [int(i) for i in os.getenv(name, "").replace(" ", "").split(",") if i]


RESOURCES = env_ids("PROJECT_STORIES_RESOURCES")
RESOURCE_TYPES = env_ids("PROJECT_STORIES_RESOURCE_TYPES")
# member ids or e-mail addresses - people who asked to stop getting these e-mails, staff
EXCLUDE_MEMBERS = [i.lower() for i in os.getenv("PROJECT_STORIES_EXCLUDE_MEMBERS", "").replace(" ", "").split(",") if i]
MIN_MINUTES = int(os.getenv("PROJECT_STORIES_MIN_MINUTES", "20"))
COOLDOWN_DAYS = int(os.getenv("PROJECT_STORIES_COOLDOWN_DAYS", "30"))
# Emails go out on workdays at this hour (Prague time), about the days since the previous workday. The cron runs
# at 7:00 and 8:00 UTC and only the run that lands on this hour sends - that stays 9:00 across summer time.
# "any" sends on every run (tests).
SEND_HOUR = os.getenv("PROJECT_STORIES_SEND_HOUR", "9")
# Nothing is sent and no member is touched unless this is explicitly turned off.
DRY_RUN = str(os.getenv("PROJECT_STORIES_DRY_RUN", "true")).lower() in ["1", "true"]

METADATA_KEY = "project_story_asked_at"
# set by the bridge when the member clicks the opt-out link in the email
OPT_OUT_KEY = "project_stories_opt_out"
PRAGUE = ZoneInfo("Europe/Prague")
PAGE_SIZE = 1000


class CustomError(Exception):
    def __init__(self, description, error_data=None):
        self.args = (description, error_data)
        self.description = description
        self.data = error_data
        super().__init__()

    def __str__(self):
        return self.description


def error_handler(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        try:
            return f(*args, **kwargs)

        except Exception:
            print(traceback.format_exc())

    return decorator


def fabman_get(path: str, params: Dict = None) -> Union[List, Dict]:
    res = requests.get(f'{FABMAN_API_URL}{path}', params=params, headers={"Authorization": f'{FABMAN_API_KEY}'})

    if res.status_code != 200:
        raise CustomError("Error during data fetching", f'{path}, {res.status_code}, {res.text[:300]}')

    return res.json()


def fabman_get_all(path: str, params: Dict) -> List[Dict]:
    """
    Fetch every page of a Fabman list endpoint.
    """
    items = []
    offset = 0

    while True:
        page = fabman_get(path, {**params, "limit": PAGE_SIZE, "offset": offset})
        items.extend(page)

        if len(page) < PAGE_SIZE:
            return items

        offset += PAGE_SIZE


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def active_minutes(log: Dict) -> int:
    """
    Minutes the machine was switched on for the member, idle time left out.
    """
    total = (parse_dt(log["stoppedAt"]) - parse_dt(log["createdAt"])).total_seconds()

    return int((total - (log.get("idleDurationSeconds") or 0)) // 60)


def watched_resources() -> Dict[int, str]:
    """
    Resource id -> name for every machine selected by PROJECT_STORIES_RESOURCES or PROJECT_STORIES_RESOURCE_TYPES.
    """
    resources = fabman_get_all("/resources", {})

    return {
        r["id"]: r["name"] for r in resources
        if (r["id"] in RESOURCES or r["type"] in RESOURCE_TYPES) and r["id"] not in NEVER_ASK
    }


def session_window(now: datetime) -> Union[tuple, None]:
    """
    (from, until) in UTC: sessions that ended since midnight of the previous workday until midnight today, so the
    email comes the next workday morning - a print finished overnight is in the member's hands by then.
    Monday covers Friday to Sunday. None when this run should not send.
    """
    local = now.astimezone(PRAGUE)

    if SEND_HOUR != "any" and (local.weekday() >= 5 or local.hour != int(SEND_HOUR)):
        return None

    today = local.replace(hour=0, minute=0, second=0, microsecond=0)
    previous_workday = today - timedelta(days=3 if local.weekday() == 0 else 1)

    # midnight in Prague, rebuilt from the date so a summer time change in between doesn't shift it by an hour
    start = datetime(previous_workday.year, previous_workday.month, previous_workday.day, tzinfo=PRAGUE)
    end = datetime(today.year, today.month, today.day, tzinfo=PRAGUE)

    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def recently_asked(member: Dict, now: datetime) -> bool:
    asked_at = (member.get("metadata") or {}).get(METADATA_KEY)

    return bool(asked_at) and parse_dt(asked_at) > now - timedelta(days=COOLDOWN_DAYS)


def excluded(member: Dict) -> bool:
    if (member.get("metadata") or {}).get(OPT_OUT_KEY):
        return True

    return str(member["id"]) in EXCLUDE_MEMBERS or (member.get("emailAddress") or "").lower() in EXCLUDE_MEMBERS


def mark_asked(member: Dict, now: datetime) -> None:
    """
    Adds the date to the member's metadata, keeping every other key. Fabman answers 409 when someone else saved
    the member since it was read (lockVersion) - then read it again and retry instead of overwriting their change.
    """
    for _ in range(3):
        metadata = dict(member.get("metadata") or {})
        metadata[METADATA_KEY] = now.isoformat()

        res = requests.put(
            f'{FABMAN_API_URL}/members/{member["id"]}',
            json={"lockVersion": member["lockVersion"], "metadata": metadata},
            headers={"Authorization": f'{FABMAN_API_KEY}'}
        )

        if res.status_code != 409:
            break

        member = fabman_get(f'/members/{member["id"]}')

    if res.status_code != 200:
        raise CustomError("Error during updating member metadata", f'{member["id"]}, {res.status_code}')


def send_project_story(member_id: int, resource_name: str, log: Dict) -> bool:
    used_on = parse_dt(log["stoppedAt"]).astimezone(PRAGUE)
    na_stroji, on_machine = machine_phrase(log["resource"])

    res = requests.post(
        f'{RAILWAY_API_URL}/project-story',
        json={
            "member_id": member_id,
            "resource": resource_name,
            "na_stroji": na_stroji,
            "on_machine": on_machine,
            "used_on": f'{used_on.day}. {used_on.month}. {used_on.year}',
            "duration_minutes": active_minutes(log)
        },
        headers={"CronjobToken": f'{CRONJOB_TOKEN}'}
    )

    # the bridge error handler answers 200 with an "Error: ..." body
    ok = res.status_code == 200 and not res.text.startswith("Error")

    if not ok:
        print(f'Error during project story email for member {member_id}')
        print(res.content)

    return ok


@error_handler
def check_project_stories():
    """
    Ask members who finished a long enough session on a watched machine what they made.
    One question per member per PROJECT_STORIES_COOLDOWN_DAYS, about their longest session in the window.
    """
    if not RESOURCES and not RESOURCE_TYPES:
        print("No machines selected - set PROJECT_STORIES_RESOURCES or PROJECT_STORIES_RESOURCE_TYPES (see list_resources)")
        return

    now = datetime.now(timezone.utc)
    window = session_window(now)

    if not window:
        print(f'Not a send run ({now.astimezone(PRAGUE):%a %H:%M} Prague) - emails go out on workdays at {SEND_HOUR}:00.')
        return

    since, until = window

    if not DRY_RUN and requests.get(f'{RAILWAY_API_URL}/health').status_code != 200:
        print(f'no healthcheck on {RAILWAY_API_URL}/health')
        return

    resources = watched_resources()

    # Fabman's "from" filters on the session start; a long print can start two days before it ends
    logs = fabman_get_all("/resource-logs", {
        "type": "allowed",
        "status": "complete",
        "from": (since - timedelta(days=2)).date().isoformat(),
        "order": "desc"
    })

    if os.getenv("TEST_USER"):
        logs = [lg for lg in logs if str(lg["member"]) == os.getenv("TEST_USER")]

    # longest qualifying session per member
    candidates = {}

    for lg in logs:
        if lg["resource"] not in resources or not lg.get("member") or not lg.get("stoppedAt"):
            continue

        if not since <= parse_dt(lg["stoppedAt"]) < until or active_minutes(lg) < MIN_MINUTES:
            continue

        best = candidates.get(lg["member"])

        if not best or active_minutes(lg) > active_minutes(best):
            candidates[lg["member"]] = lg

    sent = 0

    for member_id, lg in candidates.items():
        member = fabman_get(f'/members/{member_id}')
        resource_name = resources[lg["resource"]]

        if excluded(member):
            print(f'member {member_id} skip - opted out')
            continue

        if recently_asked(member, now):
            print(f'member {member_id} skip - asked in the last {COOLDOWN_DAYS} days')
            continue

        if DRY_RUN:
            print(f'DRY RUN: would ask member {member_id} about {resource_name} '
                  f'({machine_phrase(lg["resource"])[0]}, {active_minutes(lg)} min, log {lg["id"]})')
            continue

        if send_project_story(member_id, resource_name, lg):
            mark_asked(member, now)
            sent += 1
            print(f'project story email sent to member {member_id} ({resource_name})')

    print(f'Checked {len(logs)} sessions, {len(candidates)} qualifying members, {sent} emails sent{" (dry run)" if DRY_RUN else ""}.')


@error_handler
def list_resources():
    """
    Print machines and machine types with their Fabman ids, to fill in the env variables.
    """
    types = {t["id"]: t["name"] for t in fabman_get_all("/resource-types", {})}

    print("RESOURCE TYPES (PROJECT_STORIES_RESOURCE_TYPES):")
    for type_id, name in sorted(types.items(), key=lambda t: t[1]):
        print(f'  {type_id:>7}  {name}')

    print("RESOURCES (PROJECT_STORIES_RESOURCES):")
    for r in sorted(fabman_get_all("/resources", {}), key=lambda r: (types.get(r["type"], ""), r["name"])):
        print(f'  {r["id"]:>7}  {r["name"]}  [{types.get(r["type"], r["type"])}, {r["state"]}]')
