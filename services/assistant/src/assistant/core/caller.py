from contextvars import ContextVar

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from testee_common.http.client_ip import client_ip

# The address an MCP call came from, as the load balancer saw it: a company's API key may be
# limited to some addresses, which the api service checks when the key signs in.
CALLER_IP: ContextVar[str | None] = ContextVar("caller_ip", default=None)


class CallerAddress:
    """Keeps the request's address in CALLER_IP for the token check that runs inside it."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)

            return

        token = CALLER_IP.set(client_ip(Request(scope)))

        try:
            await self.app(scope, receive, send)
        finally:
            CALLER_IP.reset(token)
