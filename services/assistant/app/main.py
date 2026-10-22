import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prepza_common.auth import start_firebase
from prepza_common.body_limit import BodyLimitMiddleware
from prepza_common.compression import compress_answers
from prepza_common.health import health_router
from prepza_common.i18n import add_localized_errors
from prepza_common.logging import RequestLogMiddleware, configure_logging
from prepza_common.maintenance import MaintenanceMiddleware
from prepza_common.no_store import NoStoreMiddleware
from prepza_common.sentry import init_sentry
from prepza_common.shutdown import close_shared
from prepza_common.trace_prices import sync_model_prices

from app.config.settings import settings
from app.constants.transcribe import MAX_BODY_BYTES
from app.integrations.redis import get_redis
from app.routers import (
    actions,
    chat,
    connect,
    conversations,
    events,
    internal_accounts,
    mcp,
    mcp_docs,
    oauth,
    schedules,
    superadmin,
    transcribe,
)
from app.services.registry import tools
from app.storage.db import engine

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
    await sync_model_prices()

    async with mcp.running():
        yield

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
app.include_router(conversations.router)
app.include_router(actions.router)
app.include_router(events.router)
app.include_router(schedules.router)
app.include_router(internal_accounts.router)
app.include_router(connect.router)
app.include_router(mcp_docs.router)
app.include_router(superadmin.router)
# AI apps (Claude, ChatGPT, ...): the MCP endpoint and its authorization server, at the site's
# root (the gateway sends those exact paths here).
app.router.routes.extend([*oauth.routes(), *mcp.routes()])


app.include_router(health_router(engine))
