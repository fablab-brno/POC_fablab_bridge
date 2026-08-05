"""End-to-end smoke test for the FabLab bridge.

Read-only: it hits the live bridge and checks the core member-facing endpoints
respond correctly, including that Fabman auth actually works -- so a broken or
badly-rotated FABMAN_API_KEY is caught immediately instead of by an angry member.

It mutates nothing, so it is safe to run after any deploy or on a schedule.

Env vars:
  BRIDGE_BASE_URL       required, e.g. https://pocfablabbridge-production.up.railway.app
  SMOKE_TEST_MEMBER_ID  Fabman member id to probe (default 246215, the seed test user)
  X_BRIDGE_AUTH         optional; sent as the X-Bridge-Auth header so the test keeps
                        passing once ENFORCE_WEB_AUTH is turned on
  DISCORD_BOT_URL,      optional; if both are set, a failure is posted to the existing
  BRIDGE_SECRET         Discord error channel (turns this into a synthetic monitor)

Exit code: 0 = all checks pass, 1 = at least one failed.

Run locally:   BRIDGE_BASE_URL=https://... python smoke_test.py
"""
import os
import sys

import requests

BASE = os.environ["BRIDGE_BASE_URL"].rstrip("/")
MEMBER = os.getenv("SMOKE_TEST_MEMBER_ID", "246215")
TIMEOUT = 20

HEADERS = {}
if os.getenv("X_BRIDGE_AUTH"):
    HEADERS["X-Bridge-Auth"] = os.environ["X_BRIDGE_AUTH"]

results = []
_available = []


def check(name, fn):
    try:
        fn()
        results.append((name, True, ""))
        print(f"PASS  {name}")
    except Exception as e:
        results.append((name, False, str(e) or type(e).__name__))
        print(f"FAIL  {name}: {e}")


def health():
    r = requests.get(f"{BASE}/health", timeout=TIMEOUT)
    assert r.status_code == 200, f"expected 200, got {r.status_code}"


def available_trainings():
    r = requests.get(f"{BASE}/available_trainings/{MEMBER}", headers=HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"status {r.status_code}"
    assert "Error during data fetching" not in r.text, "Fabman auth/connectivity failed"
    data = r.json()
    assert isinstance(data, list), "expected a JSON list"
    _available.extend(data)


def absolved_trainings():
    r = requests.get(f"{BASE}/absolved_trainings/{MEMBER}", headers=HEADERS, timeout=TIMEOUT)
    assert r.status_code == 200, f"status {r.status_code}"
    assert "Error during data fetching" not in r.text, "Fabman auth/connectivity failed"
    assert isinstance(r.json(), list), "expected a JSON list"


def get_training_links():
    assert _available, "no available trainings to derive a training_id (upstream check failed?)"
    tid = _available[0]["id"]
    r = requests.post(
        f"{BASE}/get_training_links",
        json={"member_id": int(MEMBER), "training_id": tid},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"status {r.status_code}"
    assert r.json().get("quiz_url"), "no quiz_url in response"


def main():
    print(f"Smoke test against {BASE} (member {MEMBER})")
    check("health", health)
    check("available_trainings", available_trainings)
    check("absolved_trainings", absolved_trainings)
    check("get_training_links", get_training_links)

    failed = [name for name, ok, _ in results if not ok]
    print("---")
    print("ALL PASS" if not failed else f"FAILURES: {', '.join(failed)}")

    if failed and os.getenv("DISCORD_BOT_URL") and os.getenv("BRIDGE_SECRET"):
        try:
            requests.post(
                f'{os.environ["DISCORD_BOT_URL"]}/fabman/errors',
                json={
                    "message": "Bridge smoke test failed: " + ", ".join(failed),
                    "type": "SmokeTestFailure",
                    "stack": "\n".join(f"{n}: {msg}" for n, ok, msg in results if not ok),
                },
                params={"key": os.environ["BRIDGE_SECRET"]},
                timeout=TIMEOUT,
            )
        except Exception as e:
            print(f"(could not post failure to Discord: {e})")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
