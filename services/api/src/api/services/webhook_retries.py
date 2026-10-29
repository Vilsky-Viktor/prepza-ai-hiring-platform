import asyncio
import logging
import time
from datetime import UTC, datetime

from api.constants.api import RETRY_BATCH, RETRY_GIVE_UP, RETRY_RUN_SECONDS
from api.core.db import Session
from api.helpers.webhooks import retry_delay
from api.models.api import Webhook, WebhookRetry
from api.repositories import webhook_retries as retries
from api.repositories import webhooks
from api.services.webhooks import deliver

logger = logging.getLogger(__name__)


async def retry() -> int:
    """Every 5 minutes: events web hooks didn't take, whose time came, are sent again, a batch
    at once, batch after batch until RETRY_RUN_SECONDS into the run. One that got there since is
    dropped. One that fails again waits twice as long; after RETRY_GIVE_UP it's dropped and its
    web hook is paused. How many were due."""
    stop_at = time.monotonic() + RETRY_RUN_SECONDS
    due = 0

    while time.monotonic() < stop_at:
        sent = await retry_batch()
        due += sent

        if sent < RETRY_BATCH:
            break

    return due


async def retry_batch() -> int:
    """One batch of retries, sent at once; how many there were."""
    async with Session.begin() as session:
        claimed = await retries.claim(session, RETRY_BATCH)

    await asyncio.gather(*(resend(row, hook) for row, hook in claimed))

    return len(claimed)


async def resend(row: WebhookRetry, hook: Webhook) -> None:
    """Sends one waiting event again. Giving up drops it and pauses its web hook in one save, so
    a failure between can't leave the event dropped while the web hook still looks working."""
    async with Session() as session:
        done = await webhooks.delivered(session, hook.id, row.event_id)

    if done or await deliver(hook, row.event_id, row.body.encode()):
        async with Session.begin() as session:
            await retries.remove(session, hook.id, row.event_id)

        return

    now = datetime.now(UTC)

    if now - row.created_at >= RETRY_GIVE_UP:
        logger.warning("Web hook %s didn't take %s for days: paused", hook.id, row.event_id)

        async with Session.begin() as session:
            await retries.remove(session, hook.id, row.event_id)
            await webhooks.set_failing(session, hook.id, True)

        return

    attempts = row.attempts + 1

    async with Session.begin() as session:
        await retries.postpone(
            session, hook.id, row.event_id, attempts, now + retry_delay(attempts)
        )
