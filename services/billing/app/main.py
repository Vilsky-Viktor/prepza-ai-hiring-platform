from contextlib import asynccontextmanager

from fastapi import FastAPI
from prepza_common.auth import start_firebase
from prepza_common.body_limit import BodyLimitMiddleware
from prepza_common.health import health_router
from prepza_common.i18n import add_localized_errors
from prepza_common.logging import RequestLogMiddleware, configure_logging
from prepza_common.no_store import NoStoreMiddleware
from prepza_common.sentry import init_sentry
from prepza_common.shutdown import close_shared

from app.config.settings import settings
from app.integrations.redis import get_redis
from app.routers import (
    auto_top_ups,
    billing,
    events,
    internal,
    payment_failures,
    prices,
    schedules,
    superadmin,
    superadmin_ai,
    superadmin_limits,
)
from app.storage.db import engine

configure_logging()
init_sentry("billing")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)

    yield

    await close_shared(engine, get_redis())


app = FastAPI(
    title="billing",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
app.include_router(billing.router)
app.include_router(internal.router)
app.include_router(prices.router)
app.include_router(auto_top_ups.internal)
app.include_router(payment_failures.router)
app.include_router(superadmin.router)
app.include_router(superadmin_ai.router)
app.include_router(superadmin_limits.router)
app.include_router(events.router)
app.include_router(schedules.router)


app.include_router(health_router(engine))
