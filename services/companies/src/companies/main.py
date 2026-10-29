from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
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

from companies.api.dependencies import remember_via
from companies.api.v1 import (
    accommodations,
    account,
    ai_apps,
    allowed_domains,
    audit,
    billing,
    bulk_invites,
    candidates,
    companies,
    company_candidates,
    internal_accounts,
    internal_api,
    internal_api_changes,
    internal_api_notes,
    internal_ats,
    internal_events,
    internal_invites,
    internal_reminders,
    interview_generation,
    interview_notes,
    interview_questions,
    interviews,
    invites,
    limits,
    links,
    logos,
    maintenance,
    members,
    pause,
    reports,
    schedules,
    superadmin,
    superadmin_companies,
    superadmin_support,
    superadmin_verification,
    verification,
)
from companies.config import settings
from companies.constants.reports import MAX_BODY_BYTES
from companies.core.db import engine
from companies.integrations.redis import get_redis

configure_logging()
init_sentry("companies")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)
    yield

    await close_shared(engine, get_redis())


app = FastAPI(
    title="companies",
    # What each request came through (an AI app?), for the access checks.
    dependencies=[Depends(remember_via)],
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.api_docs else None,
)
add_localized_errors(app)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_BODY_BYTES)
compress_answers(app)
app.include_router(companies.router)
app.include_router(account.router)
app.include_router(audit.router)
app.include_router(billing.router)
app.include_router(members.router)
app.include_router(interviews.router)
app.include_router(interview_notes.router)
app.include_router(candidates.router)
app.include_router(company_candidates.router)
app.include_router(accommodations.router)
app.include_router(bulk_invites.router)
app.include_router(interview_generation.router)
app.include_router(interview_questions.router)
app.include_router(invites.router)
app.include_router(limits.router)
app.include_router(links.router)
app.include_router(logos.router)
app.include_router(reports.router)
app.include_router(verification.router)
app.include_router(internal_accounts.router)
app.include_router(internal_ats.router)
app.include_router(internal_api.router)
app.include_router(internal_api_changes.router)
app.include_router(internal_api_notes.router)
app.include_router(internal_invites.router)
app.include_router(internal_reminders.router)
app.include_router(internal_events.router)
app.include_router(schedules.router)
app.include_router(pause.router)
app.include_router(maintenance.router)
app.include_router(superadmin.router)
app.include_router(superadmin_companies.router)
app.include_router(superadmin_support.router)
app.include_router(ai_apps.router)
app.include_router(allowed_domains.router)
app.include_router(superadmin_verification.router)


app.include_router(health_router(engine))
