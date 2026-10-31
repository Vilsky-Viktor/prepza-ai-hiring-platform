import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, status
from testee_common.auth.google import Invoker
from testee_common.events import processed_events
from testee_common.limits import pause

from companies.constants.events import PROCESSED_EVENT_DAYS
from companies.core.db import Session
from companies.integrations.redis import get_redis
from companies.models.events import ProcessedEvent
from companies.services import outbox as outbox_service
from companies.services import removal_replay
from companies.services.candidate_billing import expire_unstarted
from companies.services.reminders import remind_unstarted
from companies.services.retention import delete_expired_candidates, delete_old_audit_events

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/retention", status_code=status.HTTP_204_NO_CONTENT)
async def retention() -> None:
    """Daily, from Cloud Scheduler: candidate data and audit events past their retention
    periods go, and the notes of events long processed."""
    count = await delete_expired_candidates()

    if count:
        logger.info("Deleted %d expired candidate invites", count)

    audited = await delete_old_audit_events()

    if audited:
        logger.info("Deleted %d old audit events", audited)

    # Events are remembered only while Pub/Sub may deliver them again.
    await processed_events.forget(
        Session, ProcessedEvent, datetime.now(UTC) - timedelta(days=PROCESSED_EVENT_DAYS)
    )


@router.post("/removals", status_code=status.HTTP_204_NO_CONTENT)
async def replay_removals() -> None:
    """Daily, from Cloud Scheduler, and by hand right after a database restore or clone: the
    candidates erased in the backups' life are erased again if they came back."""
    count = await removal_replay.replay()

    if count:
        logger.warning("Erased %d restored candidates again", count)


@router.post("/invite-expiry", status_code=status.HTTP_204_NO_CONTENT)
async def invite_expiry() -> None:
    """Daily, from Cloud Scheduler: invites never started expire, and their credits come back."""
    count = await expire_unstarted()

    if count:
        logger.info("Expired %d invites never started", count)


@router.post("/invite-reminders", status_code=status.HTTP_204_NO_CONTENT)
async def invite_reminders() -> None:
    """Daily, from Cloud Scheduler: candidates who haven't started get one reminder; not during
    the emergency pause (they're reminded once it's off)."""
    if await pause.is_paused(get_redis()):
        logger.warning("Reminders skipped: the emergency pause is on")

        return

    count = await remind_unstarted()

    if count:
        logger.info("Reminded %d candidates who haven't started", count)


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()
