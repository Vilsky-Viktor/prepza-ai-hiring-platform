import logging
from datetime import UTC, datetime, timedelta

from prepza_common.config.constants import DELETE_BATCH
from prepza_common.limits import pause
from prepza_common.redis import redis_lock

from generation.constants.accounts import TEXT_RETENTION_DAYS
from generation.constants.events import GENERATION_CANCELLED
from generation.constants.generation import (
    GENERATION_STOPPED,
    QUEUED_STUCK_AFTER_SECONDS,
    REVIEW_EXPIRY_DAYS,
    STUCK_AFTER_SECONDS,
)
from generation.constants.kinds import GenerationKind
from generation.constants.quality import KEY_CHECK_LOCK_KEY, KEY_CHECK_LOCK_SECONDS
from generation.core.db import Session
from generation.helpers.events import failed_event
from generation.integrations.redis import get_redis
from generation.models.generation import Generation
from generation.repositories import accounts, generations, outbox
from generation.repositories.checkpointer import delete_threads
from generation.services import batch_work
from generation.services import outbox as outbox_service
from generation.services.key_check_batches import collect_finished, submit_pending

logger = logging.getLogger(__name__)

# Cloud Scheduler calls these through routers/schedules.py; their timetable is in the
# infrastructure (and scripts/local/crontab locally).


async def key_check_batches() -> None:
    """Applies finished OpenAI batches of key checks and of other work that waits on nobody
    (translations, new options, rewritten questions), then sends the waiting ones; skipped while
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
        await batch_work.collect_finished()
        await batch_work.submit_pending()
    finally:
        await redis_lock.release(redis, KEY_CHECK_LOCK_KEY, token)


async def expire_reviews() -> None:
    """Cancels topic reviews left open for REVIEW_EXPIRY_DAYS; the event saved with each
    cancellation removes its test in companies."""
    await cancel_reviews(datetime.now(UTC) - timedelta(days=REVIEW_EXPIRY_DAYS))
    await outbox_service.flush_quietly()


async def cancel_reviews(before: datetime) -> list[Generation]:
    """Cancels up to SWEEP_BATCH reviews waiting since before `before`, each saved with the
    event that has companies remove its interview."""
    async with Session.begin() as session:
        expired = await generations.expire_reviews(session, before)

        for generation in expired:
            if generation.kind == GenerationKind.INTERVIEW:
                outbox.add(session, (GENERATION_CANCELLED, {"generation_id": str(generation.id)}))

    return expired


async def fail_stuck(running_before: datetime, queued_before: datetime) -> list[Generation]:
    """Fails up to SWEEP_BATCH generations running untouched since `running_before`, or queued
    since `queued_before`, each saved with the event that tells companies of its interview's
    failure."""
    async with Session.begin() as session:
        failed = await generations.fail_stuck(
            session, running_before, queued_before, GENERATION_STOPPED
        )

        for generation in failed:
            event = failed_event(generation)

            if event:
                outbox.add(session, event)

    return failed


async def sweep(checkpointer) -> None:
    """Fails generations whose worker died mid-job, or whose job never came, so the user can
    Retry them (a job that comes after all finds them no longer queued), and deletes
    checkpoints nothing will resume. Failed and in-review generations keep theirs."""
    now = datetime.now(UTC)
    failed = await fail_stuck(
        now - timedelta(seconds=STUCK_AFTER_SECONDS),
        now - timedelta(seconds=QUEUED_STUCK_AFTER_SECONDS),
    )

    if failed:
        logger.warning("Marked %d stuck generations as failed", len(failed))

    await expire_reviews()

    async with Session() as session:
        threads = await generations.finished_threads(session)

    for thread_id in threads:
        await checkpointer.adelete_thread(thread_id)


async def retention(checkpointer) -> None:
    """Daily: pasted job texts aren't kept longer than needed."""
    before = datetime.now(UTC) - timedelta(days=TEXT_RETENTION_DAYS)
    count = await forget_texts(before, checkpointer)

    if count:
        logger.info("Removed the pasted texts of %d old generations", count)


async def forget_texts(before: datetime, checkpointer) -> int:
    """Blanks the pasted texts of generations finished before `before`, and deletes the
    checkpoints still holding them; the saved tests stay. DELETE_BATCH at a time, each batch its
    own transaction, so a long backlog never holds one long lock. Returns how many."""
    total = 0

    while True:
        async with Session.begin() as session:
            ids = await accounts.forget_texts_batch(session, before)

        await delete_threads([str(item) for item in ids], checkpointer)
        total += len(ids)

        if len(ids) < DELETE_BATCH:
            return total


async def flush_outbox() -> int:
    """Every minute: publishes events that weren't published right after their change."""
    return await outbox_service.flush()
