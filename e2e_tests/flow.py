"""End-to-end test against the running local stack, with a real generation (needs OPENAI_API_KEY
in .env; one test of a single topic, a few cents and a few minutes).

A company generates an interview and invites a candidate, who opens the invite and takes it; the company then sees the scorecard
and pays for that candidate. Users come from the Firebase Auth emulator. The candidate uses
Resend's test address, which both Resend and mailpit accept; their invite link is read from the
companies database, since Resend's test inbox can't be read.

Usage: python3 e2e_tests/flow.py   (standard library only)
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = os.getenv("E2E_API", "http://localhost:8090/api")
AUTH = os.getenv("E2E_AUTH", "http://localhost:9199")
POSTGRES = os.getenv("E2E_POSTGRES", "prepza-postgres-1")
KIT_TEXT = "Junior Python developer: Python basics, functions and lists."
INTERVIEW_TEXT = "Backend developer: SQL basics, joins and indexes."
GENERATION_TIMEOUT = 15 * 60
# Cloudflare Turnstile's dummy token: the local test secret passes it (prepza_common human_check).
HUMAN_CHECK_TOKEN = "XXXX.DUMMY.TOKEN.XXXX"


def env(name: str) -> str:
    """From the environment, or else from the repo's .env."""
    if os.getenv(name):
        return os.environ[name]

    for line in (Path(__file__).resolve().parents[1] / ".env").read_text().splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip()

    sys.exit(f"{name} isn't set")


def call(method: str, url: str, token: str | None = None, body=None, headers=None):
    request = urllib.request.Request(
        url, data=json.dumps(body).encode() if body is not None else None, method=method
    )
    request.add_header("Content-Type", "application/json")

    for key, value in {
        **(headers or {}),
        **({"Authorization": f"Bearer {token}"} if token else {}),
    }.items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()

            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        sys.exit(f"FAIL {method} {url} -> {error.code} {error.read().decode()[:300]}")


# Billing's prices (services/billing/app/constants/credits.py).
CANDIDATE_CREDITS = 500
WELCOME_COMPANY = 3 * CANDIDATE_CREDITS


def api(method: str, path: str, token: str, body=None):
    return call(method, API + path, token, body, {"X-Human-Check": HUMAN_CHECK_TOKEN})


def step(message: str) -> None:
    print(f"- {message}", flush=True)


def check(condition: bool, message: str) -> None:
    if not condition:
        sys.exit(f"FAIL {message}")


def wait(what: str, probe, timeout: float = GENERATION_TIMEOUT, every: float = 5):
    """Polls `probe` until it returns something truthy."""
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        found = probe()

        if found:
            return found

        time.sleep(every)

    sys.exit(f"FAIL timed out waiting for {what}")


# The run's users as (local id, ID token), deleted at the end however the run ends.
CREATED: list[tuple[str, str]] = []


def sign_up(name: str, verified: bool = False, owner: bool = False) -> tuple[str, str]:
    """A new emulator user; verified ones get a fresh token carrying email_verified. Resend's test
    address takes any +label and is delivered to nobody, but all its labels are one inbox, and a
    first company's welcome credits come once per inbox: an owner gets their own, on a reserved
    domain that never receives mail."""
    suffix = uuid.uuid4().hex[:8]
    email = (
        f"e2e-{name}-{suffix}@example.com" if owner else f"delivered+e2e-{name}-{suffix}@resend.dev"
    )
    password = "secret123"
    auth = f"{AUTH}/identitytoolkit.googleapis.com/v1"
    user = call(
        "POST",
        f"{auth}/accounts:signUp?key=demo",
        body={"email": email, "password": password, "returnSecureToken": True},
    )

    if verified:
        project = env("FIREBASE_PROJECT_ID")
        call(
            "POST",
            f"{auth}/projects/{project}/accounts:update",
            body={"localId": user["localId"], "emailVerified": True},
            headers={"Authorization": "Bearer owner"},
        )
        user = call(
            "POST",
            f"{auth}/accounts:signInWithPassword?key=demo",
            body={"email": email, "password": password, "returnSecureToken": True},
        )

    CREATED.append((user["localId"], user["idToken"]))

    return email, user["idToken"]


def clean_up() -> None:
    """Deletes the run's accounts the way a user does in settings, which also deletes the
    company they alone own and their data in every service, then the emulator users. The owner
    signed up first, so it goes last, after its candidates."""
    auth = f"{AUTH}/identitytoolkit.googleapis.com/v1"
    project = env("FIREBASE_PROJECT_ID")

    for local_id, token in reversed(CREATED):
        try:
            api("DELETE", "/library/me", token)
            call(
                "POST",
                f"{auth}/projects/{project}/accounts:delete",
                body={"localId": local_id},
                headers={"Authorization": "Bearer owner"},
            )
        # A refusal (SystemExit from call) or no answer in time (OSError): the next account is
        # still deleted, and this one is left for the browser suite's clean-up of stale ones.
        except (SystemExit, OSError) as error:
            # Deleting the account removed its sign-in already.
            if "USER_NOT_FOUND" not in str(error):
                print(f"clean-up: couldn't delete a user: {error}")

    print(f"clean-up: {len(CREATED)} throwaway accounts deleted")


def invite_token(invite_id: str) -> str:
    """The token in the invite link the candidate is emailed."""
    query = f"SELECT token FROM candidate_invites WHERE id = '{invite_id}'"
    result = subprocess.run(
        ["docker", "exec", POSTGRES, "psql", "-U", "prepza", "-d", "companies", "-tAc", query],
        capture_output=True,
        text=True,
        check=True,
    )
    token = result.stdout.strip()
    check(bool(token), "the invite has a link")

    return token


def take_interview(session_id: str, token: str) -> int:
    """Takes the interview as the app does (step, answer, step, ... until it's done), answering
    every question with its first option; how many were answered."""
    answered = 0
    step = api("POST", f"/rounds/sessions/{session_id}/step", token)

    while not step["done"]:
        question = step["question"]
        answer = {"question_id": question["question_id"], "option_index": 0}
        api("POST", f"/rounds/sessions/{step['session']['id']}/answers", token, answer)
        answered += 1
        step = api("POST", f"/rounds/sessions/{session_id}/step", token)

    return answered


def company() -> None:
    _, owner = sign_up("owner", verified=True, owner=True)
    # Company names are unique across prepza, so each run gets its own.
    name = f"E2E Inc {uuid.uuid4().hex[:8]}"
    company_id = api("POST", "/companies/companies", owner, {"name": name})["id"]
    credits = f"/companies/companies/{company_id}/credits"
    check(
        api("GET", credits, owner)["available"] == WELCOME_COMPANY,
        f"a first company starts with {WELCOME_COMPANY} credits",
    )
    step(f"company created with {WELCOME_COMPANY} credits")

    interview = api(
        "POST", f"/companies/interviews?company_id={company_id}", owner, {"text": INTERVIEW_TEXT}
    )
    path = f"/companies/interviews/{interview['id']}"
    wait(
        "the interview's topics",
        lambda: api("GET", f"{path}/generation", owner).get("status") == "awaiting_review",
    )
    api("POST", f"{path}/generation/review", owner, {"selected": [0]})
    wait("the interview", lambda: api("GET", path, owner).get("set_id"))
    step("interview generated")

    email, candidate = sign_up("candidate", verified=True)
    invite = api("POST", f"{path}/candidates", owner, {"email": email})
    left = WELCOME_COMPANY - CANDIDATE_CREDITS
    check(api("GET", credits, owner)["available"] == left, "the candidate's credits are set aside")
    step(f"candidate invited; {CANDIDATE_CREDITS} credits set aside")

    token = invite_token(invite["id"])
    sessions = api("POST", f"/companies/invites/{token}/start", candidate, {"pledged": True})["sessions"]
    answered = take_interview(sessions[0]["id"], candidate)

    step(f"candidate took the interview from the invite link: {answered} answers")

    scorecard = wait(
        "the scorecard",
        lambda: (
            (row := api("GET", f"{path}/candidates/{invite['id']}", owner)).get("status")
            == "finished"
            and row
        ),
        60,
        2,
    )
    check(bool(scorecard), "the company sees the finished scorecard")
    balance = wait(
        "the charge",
        lambda: (
            (row := api("GET", f"/companies/companies/{company_id}/credits", owner))["available"]
            == left
            and row
        ),
        30,
        2,
    )
    check(balance["available"] == left, "the answered candidate is charged")
    step("scorecard ready; candidate charged")


if __name__ == "__main__":
    started = time.monotonic()
    print("company:")

    try:
        company()
    finally:
        clean_up()

    print(f"e2e ok in {time.monotonic() - started:.0f}s")
