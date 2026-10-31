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

from generation.api.v1 import (
    events,
    internal,
    internal_accounts,
    languages,
    sizes,
    superadmin,
    superadmin_additions,
    superadmin_patterns,
)
from generation.config import settings
from generation.core.db import engine
from generation.integrations.redis import get_redis

configure_logging()
init_sentry("generation")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)
    stop_loop_watch = start_loop_watch()
    await sync_model_prices()

    yield

    stop_loop_watch()
    await close_shared(engine, get_redis())


app = FastAPI(
    title="generation",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
compress_answers(app)
app.include_router(languages.router)
app.include_router(sizes.router)
app.include_router(superadmin.router)
app.include_router(superadmin_additions.router)
app.include_router(superadmin_patterns.router)
app.include_router(internal.router)
app.include_router(internal_accounts.router)
app.include_router(events.router)


app.include_router(health_router(engine))
