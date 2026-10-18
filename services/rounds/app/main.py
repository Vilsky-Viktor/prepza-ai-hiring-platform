import logging
import os
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
    help,
    help_votes,
    internal,
    internal_accounts,
    internal_maintenance,
    interview_flow,
    practice,
    schedules,
    session_feedback,
    sessions,
    superadmin,
)
from app.storage.db import engine

configure_logging()
init_sentry("rounds")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})

    if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        logger.info("LangSmith tracing enabled")

    yield

    await get_redis().aclose()
    await http.get_client().aclose()


app = FastAPI(
    title="rounds",
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
app.include_router(sessions.router)
app.include_router(interview_flow.router)
app.include_router(practice.router)
app.include_router(session_feedback.router)
app.include_router(help.router)
app.include_router(help_votes.router)
app.include_router(internal.router)
app.include_router(schedules.router)
app.include_router(superadmin.router)
app.include_router(internal_accounts.router)
app.include_router(internal_maintenance.router)


app.include_router(health_router(engine))
