from prepza_common.constants import NO_STORE, SECRET_PATH_PARAMS
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def private(request: Request) -> bool:
    """A signed-in request (an Authorization header), or one whose path carries a secret token
    (an invite's, a team invite's, an unsubscribe link's): its answer holds someone's data."""
    if "authorization" in request.headers:
        return True

    route = getattr(request.scope.get("route"), "path", "")

    return any(f"{{{name}}}" in route for name in SECRET_PATH_PARAMS)


class NoStoreMiddleware(BaseHTTPMiddleware):
    """Answers to private requests (`private`) hold someone's data: browsers and proxies are
    told not to keep them, unless the route set its own Cache-Control (a versioned logo)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if private(request) and "cache-control" not in response.headers:
            response.headers["Cache-Control"] = NO_STORE

        return response
