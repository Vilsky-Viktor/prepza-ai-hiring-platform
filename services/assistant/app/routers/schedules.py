import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, status
from prepza_common import trace_retention
from prepza_common.google import Invoker

from app.config.settings import settings
from app.constants.assistant import RETENTION_BATCH
from app.constants.mcp import IDLE_CLIENT_DAYS
from app.constants.updates import KEEP_DAYS
from app.storage import conversations, oauth, update_checks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/schedules", tags=["schedules"], dependencies=[Invoker])


@router.post("/traces", status_code=status.HTTP_204_NO_CONTENT)
async def trace_retention_job() -> None:
    """Daily, from Cloud Scheduler: every service's Langfuse traces a day short of their 30 days
    go (Langfuse's free plan has no retention of its own). Nothing without Langfuse."""
    await trace_retention.delete_old_traces()


@router.post("/retention", status_code=status.HTTP_204_NO_CONTENT)
async def retention() -> None:
    """Daily, from Cloud Scheduler: conversations nobody added to for ASSISTANT_RETENTION_DAYS
    go, with their messages and tool calls, a batch at a time until none are left; so do AI
    apps' connections whose refresh token expired, apps with no connection that registered over
    IDLE_CLIENT_DAYS ago, and get_updates checks no connection or key made in KEEP_DAYS. Safe to
    run twice at once or again: each deletes what's still there."""
    now = datetime.now(UTC)
    grants, clients = await oauth.delete_expired(now, now - timedelta(days=IDLE_CLIENT_DAYS))

    if grants or clients:
        logger.info("Deleted %d expired AI app connections and %d idle apps", grants, clients)

    checks = await update_checks.delete_before(now - timedelta(days=KEEP_DAYS))

    if checks:
        logger.info("Deleted %d stale get_updates checks", checks)

    before = now - timedelta(days=settings.assistant_retention_days)
    deleted = 0

    while True:
        batch = await conversations.delete_idle(before, RETENTION_BATCH)
        deleted += batch

        if batch < RETENTION_BATCH:
            break

    if deleted:
        logger.info("Deleted %d assistant conversations past their retention", deleted)
