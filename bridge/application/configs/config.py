import os


MAX_COURSE_ATTEMPTS = int(os.getenv("MAX_COURSE_ATTEMPTS", 3))
FERNET_KEY = os.getenv("FERNET_KEY")
FABMAN_API_KEY = os.getenv("FABMAN_API_KEY")
ECOMAIL_API_KEY = os.getenv("ECOMAIL_API_KEY")
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
CRONJOB_TOKEN = os.getenv("CRONJOB_TOKEN")
CLASSMARKER_WEBHOOK_SECRET = os.getenv("CLASSMARKER_WEBHOOK_SECRET")
FLASK_SECRET_KEY = os.getenv("SECRET_KEY")
VERIFY_CLASSMARKER_REQUESTS = str(os.getenv("VERIFY_CLASSMARKER_REQUESTS", "false")).lower() in ["1", "true"]
TRACK_TIME = os.getenv("TRACK_TIME")
DISCORD_BOT_URL = os.getenv("DISCORD_BOT_URL")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET")

# Web -> bridge shared-secret auth: the courses app sends X-Bridge-Auth == AUTH_HEADER.
# ENFORCE_WEB_AUTH off = log-but-allow rollout (unauthenticated calls are logged, not
# rejected). FABMAN_WEBHOOK_KEY gates the Fabman member-created webhook via ?key=.
AUTH_HEADER = os.getenv("AUTH_HEADER")
ENFORCE_WEB_AUTH = str(os.getenv("ENFORCE_WEB_AUTH", "false")).lower() in ["1", "true"]
FABMAN_WEBHOOK_KEY = os.getenv("FABMAN_WEBHOOK_KEY")

# COURSES_WEB_PRIVATE_KEY = os.getenv("COURSES_WEB_PRIVATE_KEY")

# Obsolete
# MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
# FABLAB_SUPPORT_EMAIL = os.getenv("FABLAB_SUPPORT_EMAIL")

ECOMAIL_MAIL_TEMPLATES = {
    "succeed_attempt": os.getenv("ECOMAIL_TEMPLATE_ID_SUCCESS_TRAINING"),
    "failed_attempt": os.getenv("ECOMAIL_TEMPLATE_ID_FAILED_TRAINING_ATTEMPT"),
    "out_of_attempts": os.getenv("ECOMAIL_TEMPLATE_ID_TRAINING_OUT_OF_ATTEMPTS"),
    "training_expiration": os.getenv("ECOMAIL_TEMPLATE_ID_TRAINING_EXPIRATION"),
    "unexpected_error": os.getenv("ECOMAIL_TEMPLATE_ID_ERROR"),
    "locked_booking": os.getenv("ECOMAIL_TEMPLATE_ID_LOCKED_BOOKING"),
    "project_story": os.getenv("ECOMAIL_TEMPLATE_ID_PROJECT_STORY")
}

ECOMAIL_SEND_EMAILS = str(os.getenv("ECOMAIL_SEND_EMAILS", True)).lower() in ["1", "true"]

# Project stories (stories/ scheduler): asks members what they made on a machine.
# A switch of its own, so the question can be stopped without touching other emails.
PROJECT_STORIES_SEND_EMAILS = str(os.getenv("PROJECT_STORIES_SEND_EMAILS", "false")).lower() in ["1", "true"]
PROJECT_STORIES_REPLY_TO = os.getenv("PROJECT_STORIES_REPLY_TO")
PROJECT_STORIES_FROM_NAME = os.getenv("PROJECT_STORIES_FROM_NAME", "Honza z FabLabu Brno")
# {na_stroji} = the machine category in the Czech 6th case from the scheduler ("na laseru"), {resource} = Fabman name
PROJECT_STORIES_SUBJECT = os.getenv("PROJECT_STORIES_SUBJECT", "Co jsi vyrobil/a {na_stroji}?")
# {email}, {member_id}, {resource} and {date} are replaced (URL-encoded) - use a Google Forms pre-filled link.
PROJECT_STORIES_FORM_URL = os.getenv("PROJECT_STORIES_FORM_URL", "https://forms.gle/RzqUZWeHa14mCwMt5")
# Base of the opt-out link in the email - the bridge's own public address.
PROJECT_STORIES_PUBLIC_URL = os.getenv("PROJECT_STORIES_PUBLIC_URL") or f'https://{os.getenv("RAILWAY_PUBLIC_DOMAIN")}'
# Fabman member metadata flag: the member clicked the opt-out link, the scheduler never asks again.
PROJECT_STORIES_OPT_OUT_KEY = "project_stories_opt_out"
