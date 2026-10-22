import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from prepza_common.auth import start_firebase
from prepza_common.body_limit import BodyLimitMiddleware
from prepza_common.company_access import remember_assistant
from prepza_common.health import health_router
from prepza_common.i18n import add_localized_errors
from prepza_common.logging import RequestLogMiddleware, configure_logging
from prepza_common.maintenance import MaintenanceMiddleware
from prepza_common.no_store import NoStoreMiddleware
from prepza_common.sentry import init_sentry
from prepza_common.shutdown import close_shared

from app.auth import MissingPermission, missing_permission
from app.config.settings import settings
from app.constants.docs import API_DESCRIPTION, API_TITLE, API_VERSION
from app.helpers.docs import name_permissions
from app.integrations import webhooks as endpoints
from app.integrations.redis import get_redis
from app.routers import (
    company,
    events,
    internal_accounts,
    internal_keys,
    manage,
    public,
    schedules,
    webhook_docs,
)
from app.storage.db import engine

configure_logging()
# httpx logs every request's full URL at INFO; a web hook's URL can carry a secret in its path.
logging.getLogger("httpx").setLevel(logging.WARNING)
init_sentry("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_firebase(settings.firebase_project_id)

    yield

    await close_shared(engine, get_redis(), endpoints.get_client())


# The reference lists the public routes only; the site's API page shows it.
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    servers=[{"url": f"{settings.site_url}/api/v1"}],
    lifespan=lifespan,
    webhooks=webhook_docs.webhooks,
    docs_url=None,
    redoc_url=None,
    # Passes the assistant's header on to companies' access checks.
    dependencies=[Depends(remember_assistant)],
)
add_localized_errors(app)
app.add_exception_handler(MissingPermission, missing_permission)
app.add_middleware(MaintenanceMiddleware, get_redis=get_redis)
app.add_middleware(NoStoreMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(BodyLimitMiddleware)
# The public routes' docs name the permission each needs.
name_permissions([*public.router.routes, *company.router.routes])
app.include_router(public.router)
app.include_router(company.router)
app.include_router(manage.router)
app.include_router(events.router)
app.include_router(internal_accounts.router)
app.include_router(internal_keys.router)
app.include_router(schedules.router)

app.include_router(health_router(engine))
