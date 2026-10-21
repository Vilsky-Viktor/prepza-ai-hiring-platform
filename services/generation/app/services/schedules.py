import logging
from datetime import UTC, datetime, timedelta

from prepza_common import pause, redis_lock

from app.constants.accounts import TEXT_RETENTION_DAYS
from app.constants.generation import (
    GENERATION_STOPPED,
    QUEUED_STUCK_AFTER_SECONDS,
    REVIEW_EXPIRY_DAYS,
    STUCK_AFTER_SECONDS,
)
from app.constants.quality import KEY_CHECK_LOCK_KEY, KEY_CHECK_LOCK_SECONDS
from app.integrations.redis import get_redis
from app.services import outbox as outbox_service
from app.services.key_check_batches import collect_finished, submit_pending
from app.storage import accounts, generations

logger = logging.getLogger(__name__)

# Cloud Scheduler calls these through routers/schedules.py; their timetable is in the
# infrastructure (and scripts/local/crontab locally).


async def key_check_batches() -> None:
    """Applies finished OpenAI batches of key checks, then sends the waiting ones; skipped while
    an earlier run is still going, and during the emergency pause (they're AI)."""
    redis = get_redis()

    if await pause.is_paused(redis):
        logger.warning("Key checks skipped: the emergency pause is on")

        return

    token = await redis_lock.acquire(redis, KEY_CHECK_LOCK_KEY, KEY_CHECK_LOCK_SECONDS)

    if token is None:
        logger.warning("Key checks are still running from the last time; skipped")

        return

    try:
        await collect_finished()
        await submit_pending()
    finally:
        await redis_lock.release(redis, KEY_CHECK_LOCK_KEY, token)


async def expire_reviews() -> None:
    """Cancels topic reviews left open for REVIEW_EXPIRY_DAYS; the event saved with each
    cancellation removes its test in companies."""
    before = datetime.now(UTC) - timedelta(days=REVIEW_EXPIRY_DAYS)

    await generations.expire_reviews(before)
    await outbox_service.flush_quietly()


async def sweep(checkpointer) -> None:
    """Fails generations whose worker died mid-job, or whose job never came, so the user can
    Retry them (a job that comes after all finds them no longer queued), and deletes
    checkpoints nothing will resume. Failed and in-review generations keep theirs."""
    now = datetime.now(UTC)
    failed = await generations.fail_stuck(
        now - timedelta(seconds=STUCK_AFTER_SECONDS),
        now - timedelta(seconds=QUEUED_STUCK_AFTER_SECONDS),
        GENERATION_STOPPED,
    )

    if failed:
        logger.warning("Marked %d stuck generations as failed", len(failed))

    await expire_reviews()

    for thread_id in await generations.finished_threads():
        await checkpointer.adelete_thread(thread_id)


async def retention(checkpointer) -> None:
    """Daily: pasted job texts aren't kept longer than needed."""
    before = datetime.now(UTC) - timedelta(days=TEXT_RETENTION_DAYS)
    count = await accounts.forget_texts(before, checkpointer)

    if count:
        logger.info("Removed the pasted texts of %d old generations", count)


async def flush_outbox() -> int:
    """Every minute: publishes events that weren't published right after their change."""
    return await outbox_service.flush()
