import sys
import os
from flask import Flask
from application.configs.config import FABMAN_API_KEY, CLASSMARKER_WEBHOOK_SECRET, FERNET_KEY, FLASK_SECRET_KEY,\
    MAIL_USERNAME, ECOMAIL_API_KEY
from application import create_app


BE_ENV = os.environ.get("BE_ENV")


def main_loop() -> None | Flask:
    host = None
    port = None

    if "--host" in sys.argv:
        host_index = sys.argv.index("--host")
        host = sys.argv[host_index + 1]

    if "--port" in sys.argv or "-p" in sys.argv:
        port_index = sys.argv.index("--port") or sys.argv.index("-p")
        port = int(sys.argv[port_index + 1])

    flask_app = create_app()

    if BE_ENV == "prod":
        return flask_app

    else:
        flask_app.run(debug=True, port=port, host=host)


if __name__ == "__main__":
    if not FABMAN_API_KEY:
        raise Exception("Missing Fabman API key")

    if not CLASSMARKER_WEBHOOK_SECRET:
        raise Exception("Missing Classmarker secret")

    if not FERNET_KEY:
        raise Exception("Missing Fernet Key secret")

    if not FLASK_SECRET_KEY:
        raise Exception("Missing Flask secret")

    if not MAIL_USERNAME:
        raise Exception("Missing email sender")

    if not ECOMAIL_API_KEY:
        raise Exception("Missing Ecomail API key")

    if BE_ENV != "prod":
        main_loop()
