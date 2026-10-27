from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.limits.maintenance import is_on

from app.integrations.redis import get_redis
from app.services import outbox as outbox_service
from app.services.session_expiry import finish_expired

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()


@router.post("/expire-interviews", status_code=status.HTTP_204_NO_CONTENT)
async def expire_interviews() -> None:
    """Every minute, from Cloud Scheduler: finishes interviews whose time ran out after the
    candidate left, so companies see them as finished. Not while maintenance mode is on:
    candidates can't answer then, and their time is given back when it's turned off."""
    if await is_on(get_redis()):
        return

    await finish_expired()
