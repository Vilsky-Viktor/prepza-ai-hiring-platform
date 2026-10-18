from contextlib import asynccontextmanager

import firebase_admin
from fastapi import FastAPI
from prepza_common import http
from prepza_common.body_limit import BodyLimitMiddleware
from prepza_common.health import health_router
from prepza_common.i18n import add_localized_errors
from prepza_common.logging import RequestLogMiddleware, configure_logging
from prepza_common.maintenance import MaintenanceMiddleware
from prepza_common.sentry import init_sentry

from app.config.settings import settings
from app.integrations.redis import get_redis
from app.routers import (
    events,
    internal_accounts,
    internal_campaigns,
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
from app.storage.db import engine

configure_logging()
init_sentry("notifications")


@asynccontextmanager
async def lifespan(app: FastAPI):
    firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})

    yield

    await http.get_client().aclose()
    await get_redis().aclose()


app = FastAPI(
    title="notifications",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
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
app.include_router(internal_campaigns.router)
app.include_router(internal_updates.router)
app.include_router(schedules.router)


app.include_router(health_router(engine))
