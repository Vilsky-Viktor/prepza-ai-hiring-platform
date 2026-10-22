import os
from functools import cache

import cachecontrol
import google.auth
import requests
from fastapi import Depends, HTTPException, Request, status
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from prepza_common.constants import GOOGLE_SCOPE, GOOGLE_TIMEOUT_SECONDS


def project() -> str:
    return os.environ["GOOGLE_CLOUD_PROJECT"]


def running_locally() -> bool:
    """Local development uses a demo- project, as the Firebase emulator requires: no Google
    Cloud, and emulators or direct calls instead of Pub/Sub, Cloud Tasks and Cloud Scheduler."""
    return project().startswith("demo-")


@cache
def credentials():
    found, _ = google.auth.default(scopes=[GOOGLE_SCOPE])

    return found


def access_token() -> str:
    """The service's own Google token (Cloud Run's service account); refreshed when stale."""
    current = credentials()

    if not current.valid:
        current.refresh(GoogleRequest())

    return current.token


class TimedRequest(GoogleRequest):
    """Google's transport, giving up after GOOGLE_TIMEOUT_SECONDS unless a call sets its own."""

    def __call__(self, url, method="GET", body=None, headers=None, timeout=None, **kwargs):
        timeout = GOOGLE_TIMEOUT_SECONDS if timeout is None else timeout

        return super().__call__(url, method, body, headers, timeout, **kwargs)


@cache
def certificate_request() -> GoogleRequest:
    """Google's transport with an HTTP cache, so its token-signing certificates are downloaded
    once per their Cache-Control lifetime, not on every call (cachecontrol comes with
    firebase-admin, which checks sign-in tokens the same way)."""
    return TimedRequest(session=cachecontrol.CacheControl(requests.Session()))


def verify_invoker(request: Request) -> None:
    """Admits only Google's calls on our behalf: Pub/Sub pushes, Cloud Tasks and Cloud
    Scheduler, all signed as the invoker service account for this service's address
    (INVOKER_SERVICE_ACCOUNT, INVOKER_AUDIENCE). Locally nothing signs, so nothing is checked."""
    if running_locally():
        return

    token = request.headers.get("Authorization", "").removeprefix("Bearer ")

    try:
        claims = id_token.verify_oauth2_token(
            token, certificate_request(), os.environ["INVOKER_AUDIENCE"]
        )
    except (ValueError, KeyError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid invoker token")

    if not claims.get("email_verified") or claims.get("email") != os.getenv(
        "INVOKER_SERVICE_ACCOUNT"
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the invoker service account")


Invoker = Depends(verify_invoker)
