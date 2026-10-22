from fastapi import HTTPException
from prepza_common.client_ip import limit_address
from prepza_common.rate_limit import hit_or_skip
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.integrations.redis import get_redis


def refusal(error: str, limited: HTTPException) -> JSONResponse:
    """A limit's refusal as an OAuth error: its status (429) and Retry-After kept."""
    body = {"error": error, "error_description": limited.detail}

    return JSONResponse(body, status_code=limited.status_code, headers=limited.headers)


class Limited:
    """An endpoint of the OAuth server counted per address against the limit named
    `per_ip`, and with `everyone`, against that limit for everyone; over a limit, refused (429)
    with an OAuth `error` and the limit's Retry-After. With Redis down, not counted rather than
    refused."""

    def __init__(
        self, app: ASGIApp, name: str, error: str, per_ip: str, everyone: str | None = None
    ):
        self.app = app
        self.name = name
        self.error = error
        self.per_ip = per_ip
        self.everyone = everyone

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["method"] in ("GET", "POST"):
            redis = get_redis()
            key = f"rate:assistant:mcp:{self.name}"

            try:
                address = limit_address(Request(scope))
                await hit_or_skip(redis, f"{key}:{address}", self.per_ip)

                if self.everyone is not None:
                    await hit_or_skip(redis, key, self.everyone)
            except HTTPException as error:
                await refusal(self.error, error)(scope, receive, send)

                return

        await self.app(scope, receive, send)


async def token_refusal(request: Request, client_id: str) -> JSONResponse | None:
    """Counts one token request of the app (a code exchange, a refresh or a revocation, whether
    its code or token turns out good or not, so guessing them is counted too) from the
    request's address; over the limit, the refusal. Counted per app and address, so someone
    naming a well-known app's public id can't use up its limit for everyone. With Redis down,
    not counted rather than refused."""
    key = f"rate:assistant:mcp:token:{client_id}:{limit_address(request)}"

    try:
        await hit_or_skip(get_redis(), key, "TOKEN_REQUESTS_PER_CLIENT_MINUTE")
    except HTTPException as error:
        return refusal("invalid_request", error)

    return None
