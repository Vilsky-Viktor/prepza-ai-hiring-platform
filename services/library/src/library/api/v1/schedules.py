import logging

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from library.services import housekeeping
from library.services import outbox as outbox_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()


@router.post("/erasures", status_code=status.HTTP_204_NO_CONTENT)
async def replay_erasures() -> None:
    """The replay of recent account deletions moved to the accounts service (its own
    /internal/schedules/erasures). Kept one release for a Cloud Scheduler job still calling
    here: it does nothing, and the next daily run reaches accounts."""
    logger.info("Erasures are replayed by accounts now")


@router.post("/bank", status_code=status.HTTP_204_NO_CONTENT)
async def daily_housekeeping() -> None:
    """Daily, from Cloud Scheduler: sends flags the verifier hasn't acted on to it again, news
    posts still missing translations to be translated again, and forgets old notes of processed
    events."""
    await housekeeping.daily()
