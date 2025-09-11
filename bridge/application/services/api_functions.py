import requests
from flask import session, Request, Response, render_template, jsonify
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os

from typing import Dict, List, Union, Tuple
from application.services.tools import get_current_training_with_index, get_member_training, expired_date
from application.configs.config import CLASSMARKER_WEBHOOK_SECRET, FABMAN_API_KEY, MAX_COURSE_ATTEMPTS, FERNET_KEY,\
    CRONJOB_TOKEN, MAIL_USERNAME, VERIFY_CLASSMARKER_REQUESTS, COURSES_WEB_PRIVATE_KEY
from ..services.error_handlers import CustomError
from ..services.extensions import mail, Message
from application.services.tools import decrypt_identifiers


def verify_payload(payload, header_hmac_signature):
    """
    Verify incoming requests.
    :param payload: requests JSON body
    :param header_hmac_signature: encoded hmac_header
    :return: result of verification as bool
    """

    dig = hmac.new(CLASSMARKER_WEBHOOK_SECRET.encode(), msg=payload, digestmod=hashlib.sha256).digest()
    calculated_signature = base64.b64encode(dig).decode().encode('ascii', 'ignore')

    return hmac.compare_digest(calculated_signature, header_hmac_signature)


def add_training_to_member(member_id: int, training_id: int) -> None:
    """
    Add absolved course to the user in Fabman.
    :param member_id: ID of current user in Fabman DB
    :param training_id: ID of current training in Fabman ID
    :raises Error during passed training posting: request failed
    :return: None
    """

    new_training_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "fromDate": datetime.now().strftime("%Y-%m-%d"),
        "trainingCourse": training_id,
        "notes": "Training absolved by Classmarker course"
    }

    res = requests.post(
        f'https://fabman.io/api/v1/members/{member_id}/trainings',
        data=new_training_data,
        headers={"Authorization": f'{FABMAN_API_KEY}'}
    )

    if res.status_code != 201:
        raise CustomError(f'Error during passed training posting - {res.text}. '
                          f'Member ID: {member_id}, data: {new_training_data}')


def parse_failed_courses_data(member_metadata: Dict[str, List[Dict[str, str | int]]], training_id: int,
                              count_attempts: bool = False, token: str = None) -> List[Dict[str, str | int]]:
    """
    CHeck attempts of failed training, add failed training to metadata od update attempts in metadata.
    :param member_metadata: fetched users metadata
    :param training_id: ID of current failed training from Fabman DB
    :param count_attempts: boolean, update or not attempts of failed training in users metadata
    :param token: Fabman API token with admin permissions
    :raises Ran out of attempts: Fail counter of training is on maximum value, user is not able to retry this quiz
    :return: list of failed courses for users metadata update
    """
    courses_cm = member_metadata.get("courses_cm") or {"failed_courses": []}
    failed_courses_list = courses_cm.get("failed_courses")

    current_course_with_index = get_current_training_with_index(failed_courses_list, training_id)

    if not count_attempts:
        return failed_courses_list

    if current_course_with_index and current_course_with_index[1]["attempts"] >= MAX_COURSE_ATTEMPTS:
        raise CustomError("Ran out of attempts")

    if not current_course_with_index:
        failed_training = data_from_get_request(f'https://fabman.io/api/v1/training-courses/{training_id}/', token)
        failed_courses_list.append({"id": training_id, "title": failed_training.get("title"), "attempts": 1})

    else:
        current_course = current_course_with_index[1]
        current_course["attempts"] += 1
        failed_courses_list[current_course_with_index[0]] = current_course

    return failed_courses_list


def process_failed_attempt(member_id: int, training_id: int, count_attempts: bool = False, token: str = None,
                           member_data: Dict = None, return_attempts: bool = False) -> Union[int, None]:
    """
    Check and update attempts for failed training.
    :param member_id: ID of current user from Fabman DB
    :param training_id: ID of current failed training from Fabman DB
    :param count_attempts: boolean, update or not attempts of failed training in users metadata
    :param token: Fabman API token with admin permissions
    :param member_data: optional dict with member data
    :param return_attempts: boolean for returning attempts of failed course
    :raises Error during failed training saving: request failed
    :return:
    """

    if not member_data:
        member_data = data_from_get_request(f'https://fabman.io/api/v1/members/{member_id}/', token)

    member_metadata = member_data.get("metadata") or {"courses_cm": {}}
    member_metadata["courses_cm"] = member_metadata.get("courses_cm") or {}
    member_metadata["courses_cm"]["failed_courses"] = parse_failed_courses_data(member_metadata, training_id,
                                                                                count_attempts, token=token)

    if count_attempts:
        new_member_data = {
            "lockVersion": member_data["lockVersion"],
            "metadata": member_metadata
        }

        res = requests.put(
            f'https://fabman.io/api/v1/members/{member_id}',
            json=new_member_data,
            headers={"Authorization": f'{FABMAN_API_KEY}'}
        )

        if res.status_code != 200:
            raise CustomError(f'Error during failed training saving - {res.text}. '
                              f'Member ID: {member_id}, data: {new_member_data}')

    if return_attempts:
        updated_fail = next(
            (f for f in member_metadata["courses_cm"]["failed_courses"] if f["id"] == training_id), {"attempts": 0}
        )

        return updated_fail["attempts"]


def remove_failed_training_from_user(member_data: Dict, member_id: int, training_id: int) -> None:
    """
    Function to remove old expired training from user when he absolved a new training.
    :param member_data: data of current user
    :param member_id: ID of current user from Fabman DB
    :param training_id: ID of expired user training from Fabman DB
    :return: None
    """

    member_metadata = member_data["metadata"] or {}
    courses_cm = member_metadata.get("courses_cm") or {"failed_courses": []}
    failed_courses_list = courses_cm.get("failed_courses")

    if failed_courses_list and any((f for f in failed_courses_list if f["id"] == training_id)):
        current_course_with_index = get_current_training_with_index(failed_courses_list, training_id)

        if current_course_with_index:
            try:
                del failed_courses_list[current_course_with_index[0]]

            except IndexError:
                pass

            new_member_data = {
                "lockVersion": member_data["lockVersion"],
                "metadata": member_metadata
            }

            res = requests.put(
                f'https://fabman.io/api/v1/members/{member_id}',
                json=new_member_data,
                headers={"Authorization": f'{FABMAN_API_KEY}'}
            )

            if res.status_code != 200:
                raise CustomError(f'Error during failed training removing from metadata - {res.text}. '
                                  f'Member ID: {member_id}, data: {new_member_data}')


def data_from_get_request(url: str, token: str) -> Union[List, Dict]:
    """
    Function for GET requests with auth header, returning fetched data.
    :param url: API URL
    :param token: Fabman API token with admin permissions
    :raises Error during data fetching: request failed
    :return: data from GET request
    """
    start = datetime.now().timestamp()
    res = requests.get(url, headers={"Authorization": f'{token}'})

    if res.status_code != 200:
        raise CustomError("Error during data fetching", f'{url}, {res.text}')

    data = res.json()
    request_name = url.replace("https://fabman.io/api/v1", "").split("?")[0]

    session.setdefault(f'fabman: {request_name}', round(datetime.now().timestamp() - start, 3))

    return data


def check_members_training(training_id: int, trainings: List[Dict]) -> str:
    """
    Find current training in members data, if exists.
    :param training_id: ID of current training in Fabman DB
    :param trainings: list of members trainings
    :raises Member has already absolved this training and it is still active: This training exists in members data
    and its untilDate value if after current day
    :return: string ID of expired training
    """

    expired_training_id = ""
    old_training = get_member_training(training_id, trainings)

    if old_training and old_training.get("untilDate"):
        if not expired_date(old_training["untilDate"]):
            print(f'Member has already absolved this training ({training_id}) and it is still active. ')

        expired_training_id = old_training["id"]

    return expired_training_id


def create_cm_link(member_id: int | str, training_id: int | str, training_list: List[Dict], token: str = None,
                   member_data: Dict = None) -> Union[str, None]:
    """
    Function for creating URLs for Classmarker, including info about user and Fabman training.
    :param member_id: ID of user in Fabman DB (/members/ API)
    :param training_id: ID of training-course in Fabman DB (/training-courses/ API)
    :param training_list: list of available trainings
    :param token: Fabman API token with admin permissions
    :param member_data: optional dict with member data
    :return: full URL of Classmarker quiz for current training and current user, empty string if user is out of attempts
    or None if some of user_id, training_id or URL in notes is missing
    """

    if not member_id or not training_id:
        print("Missing member or training ID")

        return ""

    try:
        process_failed_attempt(member_id, training_id, token=token, member_data=member_data)

    except Exception as e:
        if "Ran out of attempts" not in (e.description if isinstance(e, CustomError) else e.args):
            raise e

        return ""

    _, training = get_current_training_with_index(training_list, training_id)

    metadata = training.get("metadata") or {}
    courses_cm = metadata.get("courses_cm") or {}
    base_url = courses_cm.get("cm_url") or ""

    f = Fernet(FERNET_KEY.encode("ascii", "ignore"))
    id_string = f'{member_id}-{training_id}'
    token = f.encrypt(id_string.encode("ascii", "ignore"))

    return f'{base_url}&cm_user_id={token.decode()}' if base_url else base_url


def get_active_user_trainings_and_user_data(member_id: str, token: str) -> Tuple[List[Dict], Dict]:
    """
    Get filtered trainings of specific user without expired trainings.
    :param member_id: ID of specific member in Fabman DB
    :param token: Fabman API token with admin permissions
    :return: list of trainings of user before expiration date
    """
    data = data_from_get_request(
        f'https://fabman.io/api/v1/members/{member_id}?embed=trainings&embed=privileges',
        token
    )

    trainings = data["_embedded"]["trainings"]

    return (
        [
            {
                "id": t["trainingCourse"],
                "title": t["_embedded"]["trainingCourse"]["title"],
                "date": t["date"],
                "notes": t["_embedded"]["trainingCourse"]["notes"],
                "metadata": t["_embedded"]["trainingCourse"]["metadata"],
                "untilDate": t["untilDate"]
            } for t in trainings if (not expired_date(t["untilDate"]) if t["untilDate"] else True)
        ],
        {
            "metadata": data["metadata"],
            "privileges": data["_embedded"]["privileges"]["privileges"],
            "lockVersion": data["lockVersion"]
        }
    )


def get_training_links(request_data: Dict, token: str) -> Dict:
    """
    Get information for training's detail page
    """

    member_id = request_data.get("member_id")
    training_id = request_data.get("training_id")

    if not member_id or not training_id:
        raise ValueError("Missing member_id or training_id")

    training = data_from_get_request(f'https://fabman.io/api/v1/training-courses/{training_id}', token)

    if not training:
        raise CustomError("Training is disabled for web")

    link = create_cm_link(
        member_id,
        training_id,
        [training],
        token
    )

    courses_cm = training["metadata"].get("courses_cm") or {}

    return {
        "en_name": courses_cm.get("en_name") or training["title"],
        "cs_name": courses_cm.get("cs_name") or training["title"],
        "quiz_url": link,
        "yt_url": courses_cm.get("yt_url"),
        "wiki_url": courses_cm.get("wiki_url")
    }


def locked_bookings_fn(request: Request) -> Response:
    request_data = request.json

    if request.headers.get("CronjobToken") != CRONJOB_TOKEN:
        raise CustomError("Unauthorized access")

    locked_bookings_inner_fn(request_data)

    return Response("", 200)


def locked_bookings_inner_fn(request_data: dict) -> None:
    member_id = request_data.get("member_id")
    member_email = request_data.get("member_email")
    resource = request_data.get("resource")

    if not member_id or not member_email or not resource:
        raise ValueError("Missing member ID, email or resources name")

    # <<<---------------------- EMAIL: BOOKED RESOURCE IS LOCKED ---------------------->>>
    msg = Message("FabLab info - locked resource", sender=MAIL_USERNAME,
                  recipients=[member_email])
    msg.html = render_template(
        "locked_booking.html",
        locked_resource=resource
    )
    mail.send(msg)


def add_classmarker_training_fn(request: Request) -> Response:
    hmac_header = request.headers.get('X-Classmarker-Hmac-Sha256')
    request_data = request.json
    
    if VERIFY_CLASSMARKER_REQUESTS and not verify_payload(request.data, hmac_header.encode('ascii', 'ignore')):
        raise CustomError("Unauthorized webhook access")

    payload_status = request_data.get("payload_status")

    if payload_status == "verify":
        return Response({}, 200)

    identifiers = decrypt_identifiers(request_data["result"].get("cm_user_id"))
    member_id = int(identifiers.split("-")[0])
    training_id = int(identifiers.split("-")[1])

    member_data = data_from_get_request(
        f'https://fabman.io/api/v1/members/{member_id}?embed=trainings',
        FABMAN_API_KEY
    )

    training = data_from_get_request(
        f'https://fabman.io/api/v1/training-courses/{training_id}',
        FABMAN_API_KEY
    )

    attempts = process_failed_attempt(member_id, training_id, True, member_data=member_data,
                                      return_attempts=True, token=FABMAN_API_KEY)

    if not request_data["result"]["passed"]:
        # <<<---------------------- EMAIL: FAILED TRAINING, X ATTEMPTS LEFT---------------------->>>
        # template = "failed_attempt.html" if attempts < MAX_COURSE_ATTEMPTS else "out_of_attempts.html"
        # msg = Message("FabLab info - test failed", sender=MAIL_USERNAME, recipients=[member_data["emailAddress"]])
        # msg.html = render_template(template, training_title=training["title"])
        # mail.send(msg)

        print(f'FAILED TEST ATTEMPT - sender: {MAIL_USERNAME}, recipients: {member_data["emailAddress"]}, template_title: {training["title"]}, request: {request_data}')

        return Response("Failed attempt saved in Fabman", 200)

    expired_training_id = check_members_training(
        training_id,
        member_data["_embedded"]["trainings"] if member_data.get("_embedded") else []
    )

    add_training_to_member(member_id, training_id)

    member_data = data_from_get_request(
        f'https://fabman.io/api/v1/members/{member_id}?embed=trainings',
        FABMAN_API_KEY
    )

    remove_failed_training_from_user(member_data, member_id, training_id)

    if expired_training_id:
        res = requests.delete(
            f'https://fabman.io/api/v1/members/{member_id}/trainings/{expired_training_id}',
            headers={"Authorization": f'{FABMAN_API_KEY}'}
        )

        if res.status_code != 204:
            raise CustomError(f'Error during old training removing - {res.text}. '
                              f'Member ID: {member_id}, training ID: {expired_training_id}')

    print(f'User ID {member_id} absolved training ID {training_id}')

    # <<<---------------------- EMAIL: TRAINING PASSED ---------------------->>>
    # msg = Message("FabLab info - test passed", sender=MAIL_USERNAME, recipients=[member_data["emailAddress"]])
    # msg.html = render_template("succeed_attempt.html", training_title=training["title"])
    # mail.send(msg)
    print(f'PASSED TEST EMAIL - sender: {MAIL_USERNAME}, recipients: {member_data["emailAddress"]}, template_title: {training["title"]}, request: {request_data}')

    return Response("Training passed, updated in Fabman", 200)


def absolve_training_again_fn(request: Request) -> Response:
    request_data = request.json

    member_id = request_data.get("member_id")
    training_id = request_data.get("training_id")

    member_data = data_from_get_request(
        f'https://fabman.io/api/v1/members/{member_id}?embed=trainings',
        FABMAN_API_KEY
    )

    member_trainings = member_data["_embedded"]["trainings"]
    training = next((t for t in member_trainings if t["trainingCourse"] == training_id), None)

    try:
        training_course_url = training["_embedded"]["trainingCourse"]["metadata"]["courses_cm"]["cm_url"]

    except KeyError:
        raise CustomError(f'Unknown course quiz URL. '
                          f'Member ID: {member_id}, training ID: {training["id"]}')

    res = requests.delete(
        f'https://fabman.io/api/v1/members/{member_id}/trainings/{training["id"]}',
        headers={"Authorization": f'{FABMAN_API_KEY}'}
    )

    if res.status_code != 204:
        raise CustomError(f'Error during old training removing - {res.text}. '
                          f'Member ID: {member_id}, training ID: {training["id"]}')

    f = Fernet(FERNET_KEY.encode("ascii", "ignore"))
    id_string = f'{member_id}-{training_id}'
    token = f.encrypt(id_string.encode("ascii", "ignore"))

    quiz_url = f'{training_course_url}&cm_user_id={token.decode()}' if training_course_url else training_course_url

    return jsonify({"cm_url": quiz_url})


def get_list_of_available_trainings_fn(member_id: str) -> List[dict]:
    token = os.environ['FABMAN_API_KEY']
    user_active_trainings, user_data = get_active_user_trainings_and_user_data(member_id, token)

    trainings_url = "https://fabman.io/api/v1/training-courses"

    if user_data.get("privileges") != "admin":
        trainings_url += "?q=for_members"

    trainings = data_from_get_request(trainings_url, token)

    trainings_data = [{k: t[k] for k in ["id", "title", "metadata", "notes"]} for t in trainings]
    user_active_trainings_ids = [at["id"] for at in user_active_trainings]

    available_trainings_for_member = [t for t in trainings_data if t["id"] not in user_active_trainings_ids]
    for_render = []

    for t in available_trainings_for_member:
        t["quiz_url"] = create_cm_link(
            member_id,
            t["id"],
            available_trainings_for_member,
            token,
            member_data={"metadata": user_data["metadata"] or {}}
        )

        course_metadata = (t.get("metadata") or {}).get("courses_cm") or {}

        t["yt_url"] = course_metadata.get("yt_url") or ""
        t["for_web"] = bool(t["notes"] and "for_web" in t["notes"])
        t["for_offline"] = bool(t["notes"] and "for_offline" in t["notes"])

        t["cs_name"] = course_metadata.get("cs_name") or t["title"]
        t["en_name"] = course_metadata.get("en_name") or t["title"]

        del t["metadata"]

        for_render.append(t)

    return for_render


def training_expiration_fn(request: Request) -> Response:
    """
    Handle expiration of trainings
    """
    request_data = request.json
    member_id = request_data.get("member_id")

    if not member_id:
        raise ValueError("Missing member_id")

    if request.headers.get("CronjobToken") != CRONJOB_TOKEN:
        raise CustomError("Unauthorized access")

    public_key = hashlib.sha512(f'{member_id}{COURSES_WEB_PRIVATE_KEY}'.encode()).hexdigest()
    url = f'https://skoleni.fablabbrno.cz?id={member_id}&key={public_key}'

    member_data = data_from_get_request(f'https://fabman.io/api/v1/members/{member_id}', FABMAN_API_KEY)
    training_data = get_training_links(request_data, FABMAN_API_KEY)

    # <<<---------------------- EMAIL: TRAINING EXPIRATION ---------------------->>>
    msg = Message("FabLab info - training expiration", sender=MAIL_USERNAME, recipients=[member_data["emailAddress"]])
    msg.html = render_template(
        "training_expiration.html",
        training_title=training_data.get("title"),
        training_url=url
    )
    mail.send(msg)

    return Response("", 200)


def get_list_of_absolved_trainings_fn(member_id: str) -> List[dict]:
    token = os.environ['FABMAN_API_KEY']
    trainings = get_active_user_trainings_and_user_data(member_id, token)[0]
    res = []

    for t in trainings:
        if "metadata" in t.keys():
            course_metadata = (t.get("metadata") or {}).get("courses_cm") or {}

            t["yt_url"] = course_metadata.get("yt_url") or ""
            t["for_web"] = bool(t["notes"] and "for_web" in t["notes"])
            t["for_offline"] = bool(t["notes"] and "for_offline" in t["notes"])

            t["cs_name"] = course_metadata.get("cs_name") or t["title"]
            t["en_name"] = course_metadata.get("en_name") or t["title"]

            del t["metadata"]
            del t["notes"]

        res.append(t)

    return res


# def activities_notifications_fn(request: Request) -> Response:
#     request_data = request.json
# 
#     if request_data.get("type") != "resource_updated":
#         return Response("Not a resource update event, ignored", 200)
# 
#     event_created = request_data["createdAt"]
#     equipment_data = request_data["details"].get("resource") or {}
#     resource_status = equipment_data["state"]
# 
#     target_data = ["name", "maintenanceNotes", "updatedBy", "id"]
#     data = {key: value for key, value in equipment_data.items() if key in target_data}
#     data["createdAt"] = event_created
#     data["state"] = resource_status
# 
#     if data["state"] == "locked":
#         now = datetime.now()
#         tomorrow = now + timedelta(days=1)
# 
#         bookings = data_from_get_request(
#             f'https://fabman.io/api/v1/bookings?state=confirmed&resource={data["id"]}&fromDateTime={now.strftime("%Y-%m-%dT%H:%m")}&untilDateTime={tomorrow.strftime("%Y-%m-%dT%H:%m")}',
#             FABMAN_API_KEY
#         )
# 
#         for b in bookings:
#             member_data = data_from_get_request(f'https://fabman.io/api/v1/members/{b["member"]}', FABMAN_API_KEY)
#             resource_data = data_from_get_request(f'https://fabman.io/api/v1/resources/{data["id"]}', FABMAN_API_KEY)
# 
#             locked_bookings_inner_fn({
#                 "member_id": member_data["id"],
#                 "member_email": member_data["emailAddress"],
#                 "resource": resource_data["name"]
#             })
# 
#     return Response("LOCKED RESOURCE", 200)


def get_training_links_fn(request: Request) -> Response:
    request_data = request.json

    return jsonify(get_training_links(request_data, request.headers.get("Authorization")))
