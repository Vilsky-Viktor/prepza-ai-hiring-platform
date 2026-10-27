import logging

import httpx
from fastapi import HTTPException, Request, status
from prepza_common.http import http
from prepza_common.http.client_ip import client_ip

logger = logging.getLogger(__name__)

# Cloudflare Turnstile: the browser proves a person is there (invisibly for most), and the
# service checks the token it got with Cloudflare, once (a token works one time, for 5 minutes).
SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
# The header the browser sends the token in.
HUMAN_CHECK_HEADER = "X-Human-Check"
HUMAN_CHECK_FAILED = "Confirm you're not a robot, then try again."
SITEVERIFY_TIMEOUT_SECONDS = 10
INVALID_SECRET = "invalid-input-secret"


async def require_human(request: Request, secret: str) -> None:
    """Refuses (403) a request whose Turnstile token Cloudflare doesn't confirm. Without a
    secret (a service not set up for it), or with one Cloudflare rejects, everyone passes; so
    does everyone while Cloudflare doesn't answer: an outage or a setup mistake shouldn't stop
    hiring, and the routes keep their own rate limits."""
    if not secret:
        return

    token = request.headers.get(HUMAN_CHECK_HEADER, "")

    if not token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, HUMAN_CHECK_FAILED)

    try:
        response = await http.get_client().post(
            SITEVERIFY_URL,
            data={"secret": secret, "response": token, "remoteip": client_ip(request)},
            timeout=SITEVERIFY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        result = response.json()
    except httpx.HTTPError as error:
        logger.warning("Turnstile didn't answer, let through: %s", type(error).__name__)

        return

    # Our own secret is wrong (Terraform's "set-me" placeholder, or a typo): a setup mistake
    # never locks people out; it's reported instead.
    if INVALID_SECRET in result.get("error-codes", []):
        logger.error("Turnstile refused our secret: set turnstile-secret-key; let through")

        return

    if not result.get("success"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, HUMAN_CHECK_FAILED)
