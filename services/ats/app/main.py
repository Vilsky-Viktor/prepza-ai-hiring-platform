from contextlib import asynccontextmanager

import firebase_admin
from fastapi import FastAPI
from prepza_common import http
from prepza_common.body_limit import BodyLimitMiddleware
from prepza_common.health import health_router
from prepza_common.i18n import add_localized_errors
from prepza_common.logging import RequestLogMiddleware, configure_logging
from prepza_common.maintenance import MaintenanceMiddleware
from prepza_common.no_store import NoStoreMiddleware
from prepza_common.sentry import init_sentry

from app.config.settings import settings
from app.integrations.redis import get_redis
from app.routers import (
    ats,
    ats_connect,
    ats_webhooks,
    events,
    internal_accounts,
    internal_updates,
    schedules,
)
from app.storage.db import engine

configure_logging()
init_sentry("ats")


@asynccontextmanager
async def lifespan(app: FastAPI):
    firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})

    yield

    await http.get_client().aclose()
    await get_redis().aclose()


app = FastAPI(
    title="ats",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
app.include_router(ats_connect.router)
app.include_router(ats.router)
app.include_router(ats_webhooks.router)
app.include_router(events.router)
app.include_router(schedules.router)
app.include_router(internal_accounts.router)
app.include_router(internal_updates.router)


app.include_router(health_router(engine))
