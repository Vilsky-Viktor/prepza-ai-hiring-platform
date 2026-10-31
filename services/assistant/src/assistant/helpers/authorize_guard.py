import logging
from urllib.parse import parse_qs, urlparse

from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from testee_common.i18n.i18n import language_of, translate

from assistant.config import settings
from assistant.constants.mcp import (
    BAD_REQUEST,
    CONNECT_COOKIE,
    CONNECT_COOKIE_PATH,
    CONNECT_PATH,
    REQUEST_SECONDS,
)

logger = logging.getLogger(__name__)


def request_of(location: str) -> str | None:
    """The request id a redirect to the consent page carries."""
    url = urlparse(location)

    if url.path != CONNECT_PATH:
        return None

    return (parse_qs(url.query).get("request") or [None])[0]


def cookie(request_id: str) -> str:
    secure = "; Secure" if settings.site_url.startswith("https://") else ""

    return (
        f"{CONNECT_COOKIE}={request_id}; Path={CONNECT_COOKIE_PATH}; Max-Age={REQUEST_SECONDS};"
        f" HttpOnly; SameSite=Lax{secure}"
    )


class GuardAuthorize:
    """Wraps /authorize. Its redirect to the consent page also marks the browser that asked
    (services/connections.py approve() requires it). Any other answer it would redirect (an error,
    to the address the app registered) is a 400 page here instead, as is a request it can't read:
    /authorize never sends a browser anywhere but the consent page."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        state = {"started": False, "replaced": False}

        async def refuse(error: str) -> None:
            logger.info("Refused a request to connect: %s", error)
            language = language_of(Request(scope).headers.get("accept-language", ""))
            page = PlainTextResponse(translate(BAD_REQUEST, language), status_code=400)
            await page(scope, receive, send)

        async def guarded(message: Message) -> None:
            if state["replaced"]:
                return

            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                location = dict(headers).get(b"location", b"").decode()
                request_id = request_of(location)

                if request_id:
                    message["headers"] = [*headers, (b"set-cookie", cookie(request_id).encode())]
                elif location:
                    state["replaced"] = True
                    await refuse((parse_qs(urlparse(location).query).get("error") or ["?"])[0])

                    return

                state["started"] = True

            await send(message)

        try:
            await self.app(scope, receive, guarded)
        except Exception as error:
            if state["started"] or state["replaced"]:
                raise

            # The error's type only: its message and traceback can hold the request's values
            # (state, redirect_uri, code_challenge).
            logger.warning("A request to connect couldn't be read: %s", type(error).__name__)
            await refuse("unreadable")
