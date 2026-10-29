from contextlib import asynccontextmanager

from fastapi import FastAPI
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

from accounts.api.v1 import (
    internal_accounts,
    internal_emails,
    internal_events,
    me,
    schedules,
    superadmin_emails,
    superadmin_stats,
)
from accounts.config import settings
from accounts.core.db import engine
from accounts.integrations.redis import get_redis

configure_logging()
init_sentry("accounts")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)

    yield

    await close_shared(engine, get_redis())


app = FastAPI(
    title="accounts",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
compress_answers(app)
app.include_router(me.router)
app.include_router(superadmin_emails.router)
app.include_router(superadmin_stats.router)
app.include_router(internal_accounts.router)
app.include_router(internal_emails.router)
app.include_router(internal_events.router)
app.include_router(schedules.router)


app.include_router(health_router(engine))
