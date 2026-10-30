import logging
from datetime import UTC, datetime, timedelta

from prepza_common.events import processed_events

from library.constants.events import PROCESSED_EVENT_DAYS
from library.core.db import Session
from library.models.events import ProcessedEvent
from library.services import bank, quality

logger = logging.getLogger(__name__)


async def daily() -> None:
    """Sends flags the verifier hasn't acted on to it again, takes out of the shared bank what a
    flag, report or opt-out raced (bank.sweep), and forgets old notes of processed events (in
    batches, each its own transaction)."""
    now = datetime.now(UTC)
    resent = await quality.resend_stale_flags()
    logger.info("Sent %d flagged questions to the verifier again", resent)
    logger.info("Took %d questions out of the shared bank", await bank.sweep())
    await processed_events.forget(
        Session, ProcessedEvent, now - timedelta(days=PROCESSED_EVENT_DAYS)
    )
