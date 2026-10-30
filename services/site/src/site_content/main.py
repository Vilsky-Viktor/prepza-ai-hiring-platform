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
from prepza_common.observability.loop_watch import start_loop_watch
from prepza_common.observability.sentry import init_sentry

from site_content.api.v1 import (
    events,
    help,
    internal_accounts,
    internal_help,
    internal_news,
    news,
    schedules,
    superadmin_news,
)
from site_content.config import settings
from site_content.core.db import engine
from site_content.integrations.redis import get_redis

configure_logging()
init_sentry("site")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)
    stop_loop_watch = start_loop_watch()

    yield

    stop_loop_watch()
    await close_shared(engine, get_redis())


app = FastAPI(
    title="site",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
compress_answers(app)
app.include_router(help.router)
app.include_router(internal_help.router)
app.include_router(internal_accounts.router)
app.include_router(events.router)
app.include_router(schedules.router)
app.include_router(news.router)
app.include_router(superadmin_news.router)
app.include_router(internal_news.router)


app.include_router(health_router(engine))
