import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from testee_common.ai.trace_prices import sync_model_prices
from testee_common.auth.auth import start_firebase
from testee_common.http.body_limit import BodyLimitMiddleware
from testee_common.http.compression import compress_answers
from testee_common.http.health import health_router
from testee_common.http.no_store import NoStoreMiddleware
from testee_common.http.shutdown import close_shared
from testee_common.i18n.i18n import add_localized_errors
from testee_common.limits.maintenance import MaintenanceMiddleware
from testee_common.observability.logging import RequestLogMiddleware, configure_logging
from testee_common.observability.loop_watch import start_loop_watch
from testee_common.observability.sentry import init_sentry

from assistant.api.v1 import (
    actions,
    chat,
    connect,
    conversations,
    events,
    help_chat,
    help_votes,
    internal_accounts,
    internal_users,
    mcp,
    mcp_docs,
    oauth,
    schedules,
    superadmin,
    transcribe,
)
from assistant.config import settings
from assistant.constants.transcribe import MAX_BODY_BYTES
from assistant.core.db import engine
from assistant.integrations.redis import get_redis
from assistant.services.registry import tools

configure_logging()
# httpx logs every request's full URL at INFO; a tool's query can hold what the user searched for.
logging.getLogger("httpx").setLevel(logging.WARNING)
# Errors never carry what was said: no variables' values in their stack traces.
init_sentry("assistant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Every tool is built now: one whose route left its service's snapshot stops the start.
    tools()
    start_firebase(settings.firebase_project_id)
    stop_loop_watch = start_loop_watch()
    await sync_model_prices()

    async with mcp.running():
        yield

    stop_loop_watch()
    await close_shared(engine, get_redis())


app = FastAPI(
    title="assistant",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_BODY_BYTES)
compress_answers(app)
app.include_router(chat.router)
app.include_router(transcribe.router)
app.include_router(help_chat.router)
app.include_router(help_votes.router)
app.include_router(conversations.router)
app.include_router(actions.router)
app.include_router(events.router)
app.include_router(schedules.router)
app.include_router(internal_accounts.router)
app.include_router(internal_users.router)
app.include_router(connect.router)
app.include_router(mcp_docs.router)
app.include_router(superadmin.router)
# AI apps (Claude, ChatGPT, ...): the MCP endpoint and its authorization server, at the site's
# root (the gateway sends those exact paths here).
app.router.routes.extend([*oauth.routes(), *mcp.routes()])


app.include_router(health_router(engine))
