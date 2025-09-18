import requests
import os
from pathlib import Path

from application.services.api_functions import recognize_gender

FABMAN_API_KEY = os.getenv("FABMAN_API_KEY")
ECOMAIL_API_KEY = os.getenv("ECOMAIL_API_KEY")
LOG_PATH = Path(os.getcwd(), "log.csv")


members = []
res = [{}]
offset = 0
limit = 1000

while len(res) != 0:
    res = requests.get(
        f'https://fabman.io/api/v1/members?limit={limit}&offset={offset}',
        headers={
            "Authorization": FABMAN_API_KEY
        }
    ).json()

    members.extend([{
        "id": member.get("id"),
        "emailAddress": member.get("emailAddress"),
        "lockVersion": member.get("lockVersion"),
        "firstName": member.get("firstName"),
        "lastName": member.get("lastName")
    } for member in res])

    offset += limit

with open(LOG_PATH, "a") as log:
    log.write("ID;EMAIL;FIRST_NAME;LAST_NAME;GENDER;")

for member in members:
    email = member.get("emailAddress")

    with open(LOG_PATH, "a") as log:
        log.write(f'{member.get("id")};{email};{member.get("firstName")};{member.get("lastName")};')

    try:
        gender = recognize_gender(email, member.get("firstName"), member.get("lastName"))

        if gender is None:
            print(f'Gender not recognized for {email}')

            with open(LOG_PATH, "a") as log:
                log.write("NO GENDER;\n")

            continue

        requests.put(
            f'https://fabman.io/api/v1/members/{member.get("id")}',
            json={
                "lockVersion": member.get("lockVersion"),
                "gender": gender
            },
            headers={
                "Authorization": FABMAN_API_KEY
            }
        )

        with open(LOG_PATH, "a") as log:
            log.write(f"{gender};\n")

    except Exception as e:
        print(f'Error during {email} processing: {e}')

        with open(LOG_PATH, "a") as log:
            log.write("ERROR;\n")

        continue