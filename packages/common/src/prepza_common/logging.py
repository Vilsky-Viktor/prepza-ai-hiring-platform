import json
import logging
import os
import time
from contextvars import ContextVar
from datetime import UTC, datetime

from prepza_common.constants import TRACE_FIELD, TRACE_HEADER, UNMATCHED_ROUTE
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# The trace of the request being served, as Cloud Logging names it; None outside a request.
current_trace: ContextVar[str | None] = ContextVar("current_trace", default=None)


class JsonFormatter(logging.Formatter):
    """One JSON object per line, in the fields Cloud Logging reads: its severity, so errors are
    errors there, and the request's trace, when there is one."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace = current_trace.get()

        if trace:
            payload[TRACE_FIELD] = trace

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def trace_of(header: str | None) -> str | None:
    """The request's trace from the load balancer's header, as Cloud Logging names it; None
    without the header or outside Google Cloud."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    trace_id = (header or "").split("/")[0]

    if not project or not trace_id:
        return None

    return f"projects/{project}/traces/{trace_id}"


def route_of(request: Request) -> str:
    """The template of the route that served `request` (set once routing matched it), or
    UNMATCHED_ROUTE for a request no route took."""
    route = request.scope.get("route")

    return getattr(route, "path", None) or UNMATCHED_ROUTE


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # The HTTP client logs every request's full address at INFO, and some addresses are secrets
    # (a company's Slack web hook): only its warnings and errors are kept.
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)

    # Uvicorn's access log prints every request's full path and query and the client's address:
    # paths carry secret tokens (invite, guest and unsubscribe links) and an address is personal
    # data. RequestLogMiddleware logs each request without them.
    logging.getLogger("uvicorn.access").disabled = True


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Logs each request's line, and ties every line logged while serving it to its trace. The
    line names the route's template (`/invites/{token}`), never the path itself, which can carry
    a secret token."""

    async def dispatch(self, request: Request, call_next):
        token = current_trace.set(trace_of(request.headers.get(TRACE_HEADER)))
        start = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - start) * 1000)
            logging.getLogger("http").info(
                "%s %s %s %dms",
                request.method,
                route_of(request),
                response.status_code,
                elapsed_ms,
            )
        finally:
            current_trace.reset(token)

        return response
