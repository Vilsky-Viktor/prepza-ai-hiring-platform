from prepza_common.constants import NO_STORE
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class NoStoreMiddleware(BaseHTTPMiddleware):
    """Answers to signed-in requests (an Authorization header) hold someone's data: browsers and
    proxies are told not to keep them, unless the route set its own Cache-Control (a streamed
    answer, a versioned logo)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if "authorization" in request.headers and "cache-control" not in response.headers:
            response.headers["Cache-Control"] = NO_STORE

        return response
