from contextvars import ContextVar
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from prepza_common.config.constants import RETRY_AFTER
from prepza_common.http import http
from prepza_common.limits.limits import record_hit

from ats.constants.ats import ATS_TIMEOUT_SECONDS
from ats.integrations.errors import KeyRejected

# What an ATS answers a key it refuses: wrong, revoked, expired or missing a permission.
REJECTED = {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}
# The company whose ATS is called, for the record of the ATS's rate limit hits: the clients take
# only credentials, so whoever reads a connection's credentials (or connects one) sets it.
calling_company: ContextVar[UUID | None] = ContextVar("calling_company", default=None)


async def note_busy(response: httpx.Response, provider: str) -> None:
    """Records the ATS's 429 (too many calls) as its rate limit's hit, for the company calling."""
    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        company_id = calling_company.get()
        kind = f"provider:{provider}"
        await record_hit("ATS_RATE_LIMIT", kind=kind, scope="company", company_id=company_id)


async def send(
    method: str,
    url: str,
    headers: dict,
    unavailable: str,
    params: dict | None = None,
    body: dict | None = None,
    *,
    provider: str,
) -> httpx.Response:
    """One call to `provider`'s API; an ATS that doesn't answer is a 502 with `unavailable` (its
    name's "… didn't answer"), which the caller can retry."""
    try:
        response = await http.get_client().request(
            method, url, params=params, json=body, headers=headers, timeout=ATS_TIMEOUT_SECONDS
        )
    except httpx.HTTPError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, unavailable) from error

    await note_busy(response, provider)

    return response


def checked(
    response: httpx.Response,
    unavailable: str,
    rejected: set[int] = REJECTED,
    passes_429: bool = False,
) -> httpx.Response:
    """The ATS's answer, once it worked: a refused key raises KeyRejected; something deleted in
    the ATS (a job, a candidate), a 404, as only that is gone, not the key; with `passes_429`, a
    rate limit stays a 429 with the ATS's Retry-After (a web hook answered so is sent again
    later); anything else that
    failed is a 502 with `unavailable`."""
    if response.status_code in rejected:
        raise KeyRejected

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    if passes_429 and response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        wait = response.headers.get(RETRY_AFTER)
        headers = {RETRY_AFTER: wait} if wait else None

        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, unavailable, headers=headers)

    if not response.is_success:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, unavailable)

    return response


def next_page(url: str | None, api: str, unavailable: str) -> str | None:
    """A list's next page as the ATS's answer names it, only when it's on the ATS's own API
    (`api`: HTTPS, the same host): the call carries the key, so a link anywhere else is a 502
    with `unavailable`, never followed. None on the last page."""
    if not url:
        return None

    given, own = httpx.URL(url), httpx.URL(api)

    if given.scheme != "https" or (given.host, given.port) != (own.host, own.port):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, unavailable)

    return url


def json_of(response: httpx.Response) -> dict:
    return response.json() if response.content else {}
