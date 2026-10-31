from contextvars import ContextVar

import httpx
from testee_common.config.constants import (
    ASSISTANT_HEADER,
    REFERRAL_COOKIE,
    VIA_ASSISTANT,
    VIA_MCP,
)
from testee_common.http import http
from testee_common.http.http import bearer

from assistant.config import settings
from assistant.constants.tool_calls import REFERRAL_CODE, SERVICE_URLS, TOOL_TIMEOUT_SECONDS
from assistant.core.security import service_token

# For the MCP call being handled when an AI agent signed in with an API key: the key's company
# and id, which companies' X-Assistant header carries (it refuses any other company), and which
# each call's own token carries, as the key acts as itself.
KEY_CLAIMS: ContextVar[dict | None] = ContextVar("key_claims", default=None)


async def get(
    service: str, path: str, query: dict, token: str, language: str, via: str = VIA_ASSISTANT
) -> httpx.Response:
    """A GET to another service's user-facing route as the user, in their language."""
    return await send(service, "GET", path, query, None, token, language, via=via)


async def send(
    service: str,
    method: str,
    path: str,
    query: dict,
    body: dict | None,
    token: str,
    language: str,
    idempotency_key: str | None = None,
    via: str = VIA_ASSISTANT,
    referral: str | None = None,
) -> httpx.Response:
    """A call to another service's user-facing route as the user (or the API key), in their
    language: a read, or a write the user confirmed. Every call carries the assistant's header, signed for companies,
    naming what it came through (`via`: the assistant or an AI app): companies audits it as such
    and refuses an AI app the company doesn't allow; the other services pass it on to companies'
    access check, which refuses alike."""
    claims = KEY_CLAIMS.get()
    # An AI agent signed in with an API key calls as the key: a token signed for the service.
    signed = service_token(service, VIA_MCP, claims) if claims else token
    headers = {**bearer(signed), "Accept-Language": language}
    headers[ASSISTANT_HEADER] = service_token("companies", via, claims)

    # The referral link the user came through (their browser's cookie): a company the
    # assistant creates for them counts for the referrer, as one made on the site does.
    if service == "companies" and referral and REFERRAL_CODE.fullmatch(referral):
        headers["Cookie"] = f"{REFERRAL_COOKIE}={referral}"

    # A confirmed action's id: a service that takes the header runs it at most once.
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    return await http.get_client().request(
        method,
        getattr(settings, SERVICE_URLS[service]) + path,
        params=query,
        json=body,
        headers=headers,
        timeout=TOOL_TIMEOUT_SECONDS,
    )
