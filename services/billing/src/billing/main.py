from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from testee_common.auth.auth import start_firebase
from testee_common.auth.company_access import remember_assistant
from testee_common.http.body_limit import BodyLimitMiddleware
from testee_common.http.compression import compress_answers
from testee_common.http.health import health_router
from testee_common.http.no_store import NoStoreMiddleware
from testee_common.http.shutdown import close_shared
from testee_common.i18n.i18n import add_localized_errors
from testee_common.observability.logging import RequestLogMiddleware, configure_logging
from testee_common.observability.loop_watch import start_loop_watch
from testee_common.observability.sentry import init_sentry

from billing.api.v1 import (
    auto_top_ups,
    billing,
    company_auto_top_ups,
    company_payments,
    events,
    internal,
    prices,
    schedules,
    superadmin,
    superadmin_ai,
    superadmin_limits,
)
from billing.config import settings
from billing.core.db import engine
from billing.integrations.redis import get_redis

configure_logging()
init_sentry("billing")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)
    stop_loop_watch = start_loop_watch()

    yield

    stop_loop_watch()
    await close_shared(engine, get_redis())


app = FastAPI(
    title="billing",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
    # A company's access check passes on what the request came through (an AI app).
    dependencies=[Depends(remember_assistant)],
)
add_localized_errors(app)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
compress_answers(app)
app.include_router(billing.router)
app.include_router(internal.router)
app.include_router(prices.router)
app.include_router(auto_top_ups.internal)
app.include_router(company_payments.router)
app.include_router(company_auto_top_ups.router)
app.include_router(superadmin.router)
app.include_router(superadmin_ai.router)
app.include_router(superadmin_limits.router)
app.include_router(events.router)
app.include_router(schedules.router)


app.include_router(health_router(engine))
