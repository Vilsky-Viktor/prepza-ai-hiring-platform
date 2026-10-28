import logging
import time
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from notifications.constants.member_emails import CLEANUP_SECONDS, SENT_KEEP_DAYS
from notifications.constants.suppression import SOFT_BOUNCE_DAYS
from notifications.integrations.resend import ResendBusy
from notifications.repositories import sent_emails, soft_bounces
from notifications.services import outbox as outbox_service
from notifications.services.bulk import send_bulk
from notifications.services.digest import send_digests
from notifications.services.reminders import send_reminders

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/digest", status_code=status.HTTP_204_NO_CONTENT)
async def digest() -> None:
    """Every minute for an hour each morning, from Cloud Scheduler: the activity digest. Each
    run goes on where the last one stopped; nobody gets it twice in a day."""
    await run("digests", send_digests)


@router.post("/reminders", status_code=status.HTTP_204_NO_CONTENT)
async def reminders() -> None:
    """Every minute for an hour each morning, from Cloud Scheduler: reminders, each kind
    at most once a week to a user. The sent log's old rows go too, and soft bounces past their
    window, until CLEANUP_SECONDS after the run started; the next run deletes the rest."""
    now = datetime.now(UTC)
    until = time.monotonic() + CLEANUP_SECONDS
    await run("reminders", send_reminders)
    await sent_emails.forget(now.date() - timedelta(days=SENT_KEEP_DAYS), until)
    await soft_bounces.forget(now - timedelta(days=SOFT_BOUNCE_DAYS), until)


@router.post("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk() -> None:
    """Every minute from 08:00 to 18:59 UTC, from Cloud Scheduler: legal notices and campaigns,
    each run going on where the last one stopped; nobody gets one twice."""
    await run("bulk emails", send_bulk)


async def run(name: str, send) -> None:
    """Over Resend's per-second limit the run stops quietly: the next one goes on."""
    try:
        count = await send(datetime.now(UTC))
    except ResendBusy:
        logger.warning("Resend is busy: the next run sends the remaining %s", name)

        return

    if count:
        logger.info("Sent %d %s", count, name)


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()
