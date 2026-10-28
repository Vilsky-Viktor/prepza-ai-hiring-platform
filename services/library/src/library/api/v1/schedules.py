import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker
from prepza_common.events import processed_events

from library.constants.events import PROCESSED_EVENT_DAYS
from library.core.db import Session
from library.models.events import ProcessedEvent
from library.services import erasures as erasures_service
from library.services import news as news_service
from library.services import outbox as outbox_service
from library.services import quality as quality_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()


@router.post("/erasures", status_code=status.HTTP_204_NO_CONTENT)
async def replay_erasures() -> None:
    """Daily, from Cloud Scheduler, and by hand right after a database restore or clone: the
    accounts deleted in the backups' life are deleted again everywhere (safe to repeat)."""
    count = await erasures_service.replay()
    logger.info("Ran %d recent account deletions again", count)


@router.post("/bank", status_code=status.HTTP_204_NO_CONTENT)
async def daily_housekeeping() -> None:
    """Daily, from Cloud Scheduler: sends flags the verifier hasn't acted on to it again, news
    posts still missing translations to be translated again, and forgets old notes of processed
    events."""
    now = datetime.now(UTC)
    resent = await quality_service.resend_stale_flags()
    logger.info("Sent %d flagged questions to the verifier again", resent)
    untranslated = await news_service.resend_untranslated()
    logger.info("Sent %d news posts to be translated again", untranslated)
    await processed_events.forget(
        Session, ProcessedEvent, now - timedelta(days=PROCESSED_EVENT_DAYS)
    )
