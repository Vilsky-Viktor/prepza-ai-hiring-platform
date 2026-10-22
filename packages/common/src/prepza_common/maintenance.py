# Maintenance mode (internal_docs/compliance/post-market-monitoring-plan.md, section 4): a superadmin turns
# it on, and every service's API refuses every request with a 503, except superadmins and the
# paths in MAINTENANCE_OPEN_PATHS and MAINTENANCE_OPEN_PREFIXES. Like the emergency pause, it's
# one Redis key without expiry, with a second holding when it was turned on.
import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from prepza_common import error_codes, switches
from prepza_common.auth import verify
from prepza_common.constants import (
    MAINTENANCE,
    MAINTENANCE_CACHE_SECONDS,
    MAINTENANCE_KEY,
    MAINTENANCE_OPEN_PATHS,
    MAINTENANCE_OPEN_PREFIXES,
    MAINTENANCE_STARTED_KEY,
)
from prepza_common.i18n import request_language, translate
from prepza_common.superadmin import is_superadmin
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


async def is_on(redis) -> bool:
    """Every request asks, so each instance reads Redis at most once per
    MAINTENANCE_CACHE_SECONDS; with Redis down, the last state this instance read
    (switches.is_on)."""
    return await switches.is_on(redis, MAINTENANCE_KEY, MAINTENANCE_CACHE_SECONDS)


async def set_on(redis, on: bool, user_id: str) -> None:
    """Who switched it and when is kept in the logs."""
    if on:
        await redis.set(MAINTENANCE_KEY, user_id)
        # Turned on again while on, it keeps its first start.
        await redis.set(MAINTENANCE_STARTED_KEY, datetime.now(UTC).isoformat(), nx=True)
    else:
        await redis.delete(MAINTENANCE_KEY)

    # This instance knows at once; the others within MAINTENANCE_CACHE_SECONDS.
    switches.remember(MAINTENANCE_KEY, on, MAINTENANCE_CACHE_SECONDS)
    logger.warning("Maintenance mode turned %s by superadmin %s", "on" if on else "off", user_id)


async def take_start(redis) -> datetime | None:
    """When it was turned on, read and removed at once: only one request turning it off gets it,
    so candidates get their time back once. None when it wasn't recorded."""
    started = await redis.getdel(MAINTENANCE_STARTED_KEY)

    return datetime.fromisoformat(started.decode()) if started else None


async def put_back_start(redis, started: datetime) -> None:
    """For a turn-off that failed to give the time back: the next one gives it."""
    await redis.set(MAINTENANCE_STARTED_KEY, started.isoformat(), nx=True)


def is_open(path: str) -> bool:
    return path in MAINTENANCE_OPEN_PATHS or path.startswith(MAINTENANCE_OPEN_PREFIXES)


async def is_superadmin_request(request: Request) -> bool:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")

    if scheme.lower() != "bearer" or not token:
        return False

    # Checking the token may fetch Google's certificates: off the event loop, as FastAPI does.
    try:
        user = await run_in_threadpool(verify, token)
    except HTTPException:
        return False

    return user is not None and is_superadmin(user)


class MaintenanceMiddleware(BaseHTTPMiddleware):
    """Added in each service's main.py with the service's own Redis client."""

    def __init__(self, app, get_redis):
        super().__init__(app)
        self.get_redis = get_redis

    async def dispatch(self, request: Request, call_next):
        if is_open(request.url.path) or not await is_on(self.get_redis()):
            return await call_next(request)

        if await is_superadmin_request(request):
            return await call_next(request)

        message = translate(MAINTENANCE, request_language(request))

        return JSONResponse(
            {"detail": message, "code": error_codes.MAINTENANCE},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
