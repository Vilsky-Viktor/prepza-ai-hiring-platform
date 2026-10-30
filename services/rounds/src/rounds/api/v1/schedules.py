import time

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.limits.maintenance import is_on

from rounds.constants.voice import CLIP_UNUSED_DAYS, JOB_SECONDS
from rounds.integrations.redis import get_redis
from rounds.services import outbox as outbox_service
from rounds.services import voice_clips
from rounds.services.session_expiry import finish_expired

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


@router.post("/voice-clips", status_code=status.HTTP_204_NO_CONTENT)
async def remove_unused_clips() -> None:
    """Daily, from Cloud Scheduler: deletes the questions and phrases read aloud that nobody has
    played for CLIP_UNUSED_DAYS; a question still asked is read again when it next opens."""
    await voice_clips.remove_unused(CLIP_UNUSED_DAYS, time.monotonic() + JOB_SECONDS)
