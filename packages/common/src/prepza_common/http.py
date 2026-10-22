from collections.abc import Collection
from functools import cache

import httpx
from fastapi import HTTPException
from prepza_common.constants import HTTP_TIMEOUT_SECONDS, RETRY_AFTER, TRACE_HEADER
from prepza_common.logging import trace_header


async def pass_trace(request: httpx.Request) -> None:
    """Gives a call made while serving a request that request's trace, so one user action can be
    followed across services."""
    header = trace_header.get()

    if header and TRACE_HEADER not in request.headers:
        request.headers[TRACE_HEADER] = header


@cache
def get_client() -> httpx.AsyncClient:
    """One client per process, so calls to other services reuse their connections; each call
    carries the trace of the request being served. It retries nothing (constants.py)."""
    return httpx.AsyncClient(
        timeout=HTTP_TIMEOUT_SECONDS,
        event_hooks={"request": [pass_trace]},
    )


def bearer(token: str) -> dict[str, str]:
    """The Authorization header carrying `token`: another service's, a user's, or a provider's
    key."""
    return {"Authorization": f"Bearer {token}"}


def passed_on(response: httpx.Response, codes: Collection[int] | None = None) -> httpx.Response:
    """Another service's answer, once it worked. Its refusals in `codes` (any refusal, without
    them) reach the client unchanged, status, reason and Retry-After; another failure raises."""
    refused = response.is_error if codes is None else response.status_code in codes

    if refused:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = None

        retry_after = response.headers.get(RETRY_AFTER)
        headers = {RETRY_AFTER: retry_after} if retry_after else None

        raise HTTPException(response.status_code, detail, headers=headers)

    if response.is_error:
        response.raise_for_status()

    return response
