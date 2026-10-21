from fastapi import HTTPException
from mcp.server.auth.provider import TokenError
from prepza_common.client_ip import client_ip
from prepza_common.rate_limit import hit_or_skip
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.integrations.redis import get_redis


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
                address = client_ip(Request(scope))
                await hit_or_skip(redis, f"{key}:{address}", self.per_ip)

                if self.everyone is not None:
                    await hit_or_skip(redis, key, self.everyone)
            except HTTPException as error:
                body = {"error": self.error, "error_description": error.detail}
                refused = JSONResponse(body, status_code=error.status_code, headers=error.headers)
                await refused(scope, receive, send)

                return

        await self.app(scope, receive, send)


async def limit_tokens(client_id: str) -> None:
    """Counts one token request of the app; over the limit, refused. With Redis down, not
    counted rather than refused."""
    key = f"rate:assistant:mcp:token:{client_id}"

    try:
        await hit_or_skip(get_redis(), key, "TOKEN_REQUESTS_PER_CLIENT_MINUTE")
    except HTTPException:
        raise TokenError("invalid_request", "Too many token requests; try again in a minute.")
