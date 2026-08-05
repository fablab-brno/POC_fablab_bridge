from functools import wraps
from hmac import compare_digest

from flask import request

from ..configs.config import AUTH_HEADER, ENFORCE_WEB_AUTH, FABMAN_WEBHOOK_KEY
from .error_handlers import CustomError


def _matches(provided: str, expected: str) -> bool:
    """Constant-time secret comparison that tolerates missing values."""
    return bool(provided) and bool(expected) and compare_digest(provided, expected)


def require_web_auth(f):
    """Require the shared X-Bridge-Auth secret from the courses web app.

    Rolls out as log-but-allow: an unauthenticated call is logged but still
    served until ENFORCE_WEB_AUTH is set, so nothing breaks before the web app
    starts sending the header.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        if not _matches(request.headers.get("X-Bridge-Auth"), AUTH_HEADER):
            if ENFORCE_WEB_AUTH:
                raise CustomError("Unauthorized access")

            print(f"[web-auth] log-but-allow: missing/invalid X-Bridge-Auth on "
                  f"{request.method} {request.path}", flush=True)

        return f(*args, **kwargs)

    return decorator


def require_fabman_webhook_key(f):
    """Require ?key=FABMAN_WEBHOOK_KEY on the Fabman member-created webhook.

    Log-but-allow, same rollout as require_web_auth.
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        if not _matches(request.args.get("key"), FABMAN_WEBHOOK_KEY):
            if ENFORCE_WEB_AUTH:
                raise CustomError("Unauthorized access")

            print(f"[fabman-webhook] log-but-allow: missing/invalid key on {request.path}", flush=True)

        return f(*args, **kwargs)

    return decorator
