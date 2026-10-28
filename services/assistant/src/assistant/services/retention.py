import logging
from datetime import UTC, datetime, timedelta

from assistant.config import settings
from assistant.constants.assistant import RETENTION_BATCH
from assistant.constants.mcp import IDLE_CLIENT_DAYS
from assistant.constants.updates import KEEP_DAYS
from assistant.core.db import Session
from assistant.repositories import conversations, oauth, update_checks

logger = logging.getLogger(__name__)


async def delete_old() -> None:
    """Expired AI app connections and idle apps, stale get_updates checks, then conversations
    past their retention: each a batch at a time, each batch its own transaction, until none
    are left. Safe to run twice at once or again: each deletes what's still there."""
    now = datetime.now(UTC)
    grants, clients = await oauth.delete_expired(
        Session, now, now - timedelta(days=IDLE_CLIENT_DAYS)
    )

    if grants or clients:
        logger.info("Deleted %d expired AI app connections and %d idle apps", grants, clients)

    checks = await update_checks.delete_before(Session, now - timedelta(days=KEEP_DAYS))

    if checks:
        logger.info("Deleted %d stale get_updates checks", checks)

    before = now - timedelta(days=settings.assistant_retention_days)
    deleted = 0

    while True:
        async with Session.begin() as session:
            batch = await conversations.delete_idle(session, before, RETENTION_BATCH)

        deleted += batch

        if batch < RETENTION_BATCH:
            break

    if deleted:
        logger.info("Deleted %d assistant conversations past their retention", deleted)
