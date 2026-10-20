import logging
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
    firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})

    yield

    await http.get_client().aclose()
    await endpoints.get_client().aclose()
    await get_redis().aclose()


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
