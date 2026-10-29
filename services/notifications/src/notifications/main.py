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
from prepza_common.observability.sentry import init_sentry

from notifications.api.v1 import (
    events,
    internal_accounts,
    internal_updates,
    me,
    schedules,
    slack,
    superadmin,
    superadmin_campaigns,
    superadmin_legal,
    superadmin_suppressed,
    unsubscribe,
    webhooks,
)
from notifications.config import settings
from notifications.core.db import engine
from notifications.integrations.redis import get_redis

configure_logging()
init_sentry("notifications")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)

    yield

    await close_shared(engine, get_redis())


app = FastAPI(
    title="notifications",
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
app.include_router(me.router)
app.include_router(events.router)
app.include_router(webhooks.router)
app.include_router(internal_accounts.router)
app.include_router(slack.router)
app.include_router(unsubscribe.router)
app.include_router(superadmin.router)
app.include_router(superadmin_legal.router)
app.include_router(superadmin_campaigns.router)
app.include_router(superadmin_suppressed.router)
app.include_router(internal_updates.router)
app.include_router(schedules.router)


app.include_router(health_router(engine))
