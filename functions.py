import os
import requests
import hmac
import hashlib
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from typing import Dict, List, Union, Tuple
from tools import get_current_training_with_index, get_member_training, expired_date


MAX_COURSE_ATTEMPTS = os.environ.get("MAX_COURSE_ATTEMPTS", default=3)
FERNET_KEY = os.environ.get("FERNET_KEY", default="")
FABMAN_API_KEY = os.environ.get("FABMAN_API_KEY", default="")
CLASSMARKER_WEBHOOK_SECRET = os.environ.get("CLASSMARKER_WEBHOOK_SECRET", default="")


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
        raise Exception("Error during passed training posting")


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

    failed_courses_list = member_metadata.get("failed_courses") or []
    current_course_with_index = get_current_training_with_index(failed_courses_list, training_id)

    if current_course_with_index and current_course_with_index[1]["attempts"] >= MAX_COURSE_ATTEMPTS:
        raise Exception("Ran out of attempts")

    if not count_attempts:
        return failed_courses_list

    if not current_course_with_index:
        failed_training = data_from_get_request(f'https://fabman.io/api/v1/training-courses/{training_id}/', token)
        failed_courses_list.append({"id": training_id, "title": failed_training.get("title"), "attempts": 1})

    else:
        current_course = current_course_with_index[1]
        current_course["attempts"] += 1
        failed_courses_list[current_course_with_index[0]] = current_course

    return failed_courses_list


def process_failed_attempt(member_id: int, training_id: int, count_attempts: bool = False, token: str = None) -> None:
    """
    Check and update attempts for failed training.
    :param member_id: ID of current user from Fabman DB
    :param training_id: ID of current failed training from Fabman DB
    :param count_attempts: boolean, update or not attempts of failed training in users metadata
    :param token: Fabman API token with admin permissions
    :raises Error during failed training saving: request failed
    :return:
    """

    member_data = data_from_get_request(f'https://fabman.io/api/v1/members/{member_id}/', token)

    member_metadata = member_data.get("metadata") or {}
    member_metadata["failed_courses"] = parse_failed_courses_data(member_metadata, training_id, count_attempts)

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
            raise Exception("Error during failed training saving")


def remove_failed_training_from_user(member_data: Dict, member_id: int, training_id: int) -> None:
    """
    Function to remove old expired training from user when he absolved a new training.
    :param member_data: data of current user
    :param member_id: ID of current user from Fabman DB
    :param training_id: ID of expired user training from Fabman DB
    :return: None
    """

    member_metadata = member_data["metadata"]
    failed_courses_list = member_metadata.get("failed_courses")

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
                raise Exception("Error during failed training removing from metadata")


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
        raise Exception("Error during data fetching")

    data = res.json()

    if "/training-courses" in url:
        if isinstance(data, list):
            return [t for t in data if not (t.get("metadata") or {}).get("not_online")]

        return data if not (data.get("metadata") or {}).get("not_online") else {}

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
            raise Exception("Member has already absolved this training and it is still active")

        expired_training_id = old_training["id"]

    return expired_training_id


def create_cm_link(
        member_id: int | str, training_id: int | str, training_list: List[Dict], token: str = None
) -> Union[str, None]:
    """
    Function for creating URLs for Classmarker, including info about user and Fabman training.
    :param member_id: ID of user in Fabman DB (/members/ API)
    :param training_id: ID of training-course in Fabman DB (/training-courses/ API)
    :param training_list: list of available trainings
    :param token: Fabman API token with admin permissions
    :return: full URL of Classmarker quiz for current training and current user, empty string if user is out of attempts
    or None if some of user_id, training_id or URL in notes is missing
    """

    if not member_id or not training_id:
        print("Missing member or training ID")

        return ""

    try:
        process_failed_attempt(member_id, training_id, token=token)

    except Exception as e:
        if "Ran out of attempts" not in e.args:
            # <<<---------------------- EMAIL: FAILED TRAINING, OUT OF ATTEMPTS---------------------->>>

            raise e

        return ""

    index, training = get_current_training_with_index(training_list, training_id)
    base_url = (training.get("metadata") or {}).get("cm_url") or ""

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

    return [t for t in trainings if (not expired_date(t["untilDate"]) if t["untilDate"] else True)], data
