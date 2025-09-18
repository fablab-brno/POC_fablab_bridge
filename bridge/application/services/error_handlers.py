from flask import Response, request
import traceback
from functools import wraps
from typing import List
import requests

# from ..services.extensions import mail, Message
from ..configs.config import FABMAN_API_KEY, DISCORD_BOT_URL, BRIDGE_SECRET


ERROR_WHITELIST = [
    "Ran out of attempts",
    "Training is disabled for web"
]


class CustomError(Exception):
    def __init__(self, description, error_data=None):
        self.args = (description, error_data)
        self.description = description
        self.data = error_data
        super().__init__()

    def __str__(self):
        return self.description


def handle_exception(fn_name: str, e: Exception, error_stack: List[str], member_id: int = None) -> Response:
    from ..services.api_functions import data_from_get_request

    error = f'{e.__class__.__name__}: {str(e)}'
    stack = "\n".join(error_stack)

    if fn_name == "add_classmarker_training" and str(e) not in ERROR_WHITELIST:
        user_email = None

        try:
            if member_id:
                from .api_functions import send_email

                member_data = data_from_get_request(f'https://fabman.io/api/v1/members/{member_id}', FABMAN_API_KEY)
                user_email = member_data["emailAddress"]

                if not user_email:
                    raise ValueError("Empty user email in error handler")

                send_email([user_email], f'Fablab info - process error', "unexpected_error")

                # msg = Message("Fablab info - process error", sender=MAIL_USERNAME, recipients=[user_email])
                # msg.html = render_template("unexpected_error.html")
                # mail.send(msg)

        except Exception:
            error_stack.append("ERROR DURING SENDING FAIL EMAIL TO USER:")
            error_stack.extend(traceback.format_exc().split("\n"))


        # msg = Message("Fablab info - process error", sender=MAIL_USERNAME, recipients=[FABLAB_SUPPORT_EMAIL])
        # msg.html = render_template(
        #     "unexpected_error_support.html",
        #     user_email=user_email,
        #     error_stack=error_stack
        # )
        # mail.send(msg)

    print(stack)

    requests.post(
        f'{DISCORD_BOT_URL}/fabman/errors',
        json={
            "message": e.args[0],
            "type": type(e).__name__,
            "stack": stack
        },
        params={"key": BRIDGE_SECRET}
,
    )

    return Response(f'Error: {error}, for more information check applications log', 200)


def error_handler(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        from ..services.tools import decrypt_identifiers

        try:
            return f(*args, **kwargs)

        except Exception as e:
            member_id = request.json.get("member_id") if request.method.lower() != "get" else None

            error_stack = traceback.format_exc().split("\n")

            if request.path == "/add_classmarker_training":
                try:
                    identifiers = decrypt_identifiers(request.json["result"].get("cm_user_id"))
                    member_id = int(identifiers.split("-")[0])

                except CustomError:
                    error_stack.append("ERROR DURING PARSING IDENTIFIERS IN ERROR HANDLER")
                    error_stack.extend(traceback.format_exc().split("\n"))

            return handle_exception(f.__name__, e, error_stack, member_id)

    return decorator
