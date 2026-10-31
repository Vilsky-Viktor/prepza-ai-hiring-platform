import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncEngine
from testee_common.config.constants import NOT_READY
from testee_common.db.db import ping

logger = logging.getLogger(__name__)


def health_router(engine: AsyncEngine) -> APIRouter:
    """A service's /health, that it answers, and /ready, once its database answers too: Docker's
    healthcheck and the startup probe use it. Redis isn't checked: an outage there shouldn't
    stop a service from starting."""
    router = APIRouter(include_in_schema=False)

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @router.get("/ready")
    async def ready() -> dict:
        try:
            await ping(engine)
        except Exception:
            logger.exception(NOT_READY)

            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, NOT_READY)

        return {"status": "ready"}

    return router
