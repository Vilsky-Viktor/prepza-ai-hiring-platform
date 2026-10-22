import json

from prepza_common import error_codes
from prepza_common.constants import BODY_TOO_LARGE, MAX_BODY_BYTES
from prepza_common.i18n import language_of, translate


class TooLarge(Exception):
    pass


class BodyLimitMiddleware:
    """Refuses a request whose body is over `max_bytes` with a 413, in the request's language,
    whether it says its size (Content-Length) or not (streamed), before more of it is read: a
    huge body can't run a service out of memory. Plain ASGI, so it counts the body as it
    arrives."""

    def __init__(self, app, max_bytes: int = MAX_BODY_BYTES):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope["headers"])
        language = headers.get(b"accept-language", b"").decode("latin-1")

        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = 0

        if declared > self.max_bytes:
            return await refuse(send, language)

        received = 0
        started = False

        async def counted_receive():
            nonlocal received
            message = await receive()

            if message["type"] == "http.request":
                received += len(message.get("body", b""))

                if received > self.max_bytes:
                    raise TooLarge

            return message

        async def watched_send(message):
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, counted_receive, watched_send)
        except TooLarge:
            if not started:
                await refuse(send, language)


async def refuse(send, accept_language: str) -> None:
    detail = translate(BODY_TOO_LARGE, language_of(accept_language))
    body = json.dumps({"detail": detail, "code": error_codes.BODY_TOO_LARGE}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
