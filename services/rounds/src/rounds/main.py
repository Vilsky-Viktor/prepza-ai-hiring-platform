from contextlib import asynccontextmanager

from fastapi import FastAPI
from prepza_common.ai.trace_prices import sync_model_prices
from prepza_common.auth.auth import start_firebase
from prepza_common.http.body_limit import BodyLimitMiddleware
from prepza_common.http.compression import compress_answers
from prepza_common.http.health import health_router
from prepza_common.http.no_store import NoStoreMiddleware
from prepza_common.http.shutdown import close_shared
from prepza_common.i18n.i18n import add_localized_errors
from prepza_common.limits.maintenance import MaintenanceMiddleware
from prepza_common.observability.logging import RequestLogMiddleware, configure_logging
from prepza_common.observability.sentry import init_sentry

from rounds.api.v1 import (
    events,
    help,
    help_votes,
    internal,
    internal_accounts,
    internal_maintenance,
    interview_flow,
    practice,
    schedules,
    session_feedback,
    sessions,
    superadmin,
)
from rounds.config import settings
from rounds.core.db import engine
from rounds.integrations.redis import get_redis

configure_logging()
init_sentry("rounds")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)
    await sync_model_prices()

    yield

    await close_shared(engine, get_redis())


app = FastAPI(
    title="rounds",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
compress_answers(app)
app.include_router(sessions.router)
app.include_router(interview_flow.router)
app.include_router(practice.router)
app.include_router(session_feedback.router)
app.include_router(help.router)
app.include_router(help_votes.router)
app.include_router(internal.router)
app.include_router(events.router)
app.include_router(schedules.router)
app.include_router(superadmin.router)
app.include_router(internal_accounts.router)
app.include_router(internal_maintenance.router)


app.include_router(health_router(engine))
