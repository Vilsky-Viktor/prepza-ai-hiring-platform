import logging
from datetime import UTC, datetime, timedelta

from prepza_common.events import processed_events

from library.constants.events import PROCESSED_EVENT_DAYS
from library.core.db import Session
from library.models.events import ProcessedEvent
from library.services import news, quality

logger = logging.getLogger(__name__)


async def daily() -> None:
    """Sends flags the verifier hasn't acted on to it again, news posts still missing
    translations to be translated again, and forgets old notes of processed events (in
    batches, each its own transaction)."""
    now = datetime.now(UTC)
    resent = await quality.resend_stale_flags()
    logger.info("Sent %d flagged questions to the verifier again", resent)
    untranslated = await news.resend_untranslated()
    logger.info("Sent %d news posts to be translated again", untranslated)
    await processed_events.forget(
        Session, ProcessedEvent, now - timedelta(days=PROCESSED_EVENT_DAYS)
    )
