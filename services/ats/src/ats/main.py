from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from prepza_common.auth.auth import start_firebase
from prepza_common.auth.company_access import remember_assistant
from prepza_common.http.body_limit import BodyLimitMiddleware
from prepza_common.http.compression import compress_answers
from prepza_common.http.health import health_router
from prepza_common.http.no_store import NoStoreMiddleware
from prepza_common.http.shutdown import close_shared
from prepza_common.i18n.i18n import add_localized_errors
from prepza_common.limits.maintenance import MaintenanceMiddleware
from prepza_common.observability.logging import RequestLogMiddleware, configure_logging
from prepza_common.observability.loop_watch import start_loop_watch
from prepza_common.observability.sentry import init_sentry

from ats.api.v1 import (
    ats,
    ats_connect,
    ats_webhooks,
    events,
    internal_accounts,
    internal_companies,
    internal_updates,
    schedules,
)
from ats.config import settings
from ats.core.db import engine
from ats.integrations.redis import get_redis

configure_logging()
init_sentry("ats")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)
    stop_loop_watch = start_loop_watch()

    yield

    stop_loop_watch()
    await close_shared(engine, get_redis())


app = FastAPI(
    title="ats",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
    # Passes the assistant's header on to companies' access checks.
    dependencies=[Depends(remember_assistant)],
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
compress_answers(app)
app.include_router(ats_connect.router)
app.include_router(ats.router)
app.include_router(ats_webhooks.router)
app.include_router(events.router)
app.include_router(schedules.router)
app.include_router(internal_accounts.router)
app.include_router(internal_updates.router)
app.include_router(internal_companies.router)


app.include_router(health_router(engine))
