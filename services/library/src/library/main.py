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

from library.api.v1 import (
    internal,
    internal_accounts,
    internal_additions,
    internal_code,
    internal_emails,
    internal_events,
    internal_feedback,
    internal_news,
    internal_practice,
    internal_quality,
    internal_reuse,
    me,
    news,
    schedules,
    superadmin,
    superadmin_emails,
    superadmin_news,
    superadmin_quality,
    superadmin_stats,
    templates,
)
from library.config import settings
from library.core.db import engine
from library.integrations.redis import get_redis

configure_logging()
init_sentry("library")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)
    yield

    await close_shared(engine, get_redis())


app = FastAPI(
    title="library",
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
app.include_router(superadmin.router)
app.include_router(superadmin_emails.router)
app.include_router(superadmin_news.router)
app.include_router(superadmin_quality.router)
app.include_router(superadmin_stats.router)
app.include_router(templates.router)
app.include_router(news.router)
app.include_router(internal.router)
app.include_router(internal_emails.router)
app.include_router(internal_accounts.router)
app.include_router(internal_additions.router)
app.include_router(schedules.router)
app.include_router(internal_events.router)
app.include_router(internal_feedback.router)
app.include_router(internal_news.router)
app.include_router(internal_practice.router)
app.include_router(internal_quality.router)
app.include_router(internal_reuse.router)
app.include_router(internal_code.router)


app.include_router(health_router(engine))
