import logging
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime, timedelta

import httpx
from prepza_common import pubsub
from prepza_common.constants import (
    HTTP_TIMEOUT_SECONDS,
    OUTBOX_BATCH,
    OUTBOX_FLUSH_SECONDS,
    OUTBOX_KEEP_DAYS,
    OUTBOX_MAX_ATTEMPTS,
    OUTBOX_REJECTED_STATUSES,
    PUBLISH_IN_REQUEST_TIMEOUT_SECONDS,
)
from prepza_common.db import delete_in_batches
from sqlalchemy import select

logger = logging.getLogger(__name__)

# The ids of the events the current request (or job) saved, so that flush_quietly publishes
# only those and leaves older ones to the scheduled flush.
saved_ids: ContextVar[list[uuid.UUID] | None] = ContextVar("outbox_saved_ids", default=None)


def add(session, model, event_type: str, data: dict) -> None:
    """Saves an event in the caller's transaction, so it exists exactly when the change does.
    Its row id goes with it as the event's id (pubsub.EVENT_ID_ATTRIBUTE)."""
    row = model(id=uuid.uuid4(), event_type=event_type, data=data)
    session.add(row)
    saved = saved_ids.get()

    if saved is None:
        saved = []
        saved_ids.set(saved)

    saved.append(row.id)


def rejected(error: Exception) -> bool:
    """Pub/Sub refused the messages themselves, rather than being down or out of reach."""
    return (
        isinstance(error, httpx.HTTPStatusError)
        and error.response.status_code in OUTBOX_REJECTED_STATUSES
    )


def count_rejection(row, error: Exception) -> None:
    row.attempts += 1

    if row.attempts >= OUTBOX_MAX_ATTEMPTS:
        # Parked: no flush tries it again. Setting attempts back to 0 sends it once fixed. Logged
        # as an error, so Sentry reports it (its logging integration sends errors).
        logger.error("Outbox event %s (%s) parked: %s", row.id, row.event_type, error)
    else:
        logger.warning("Pub/Sub rejected outbox event %s (%s): %s", row.id, row.event_type, error)


async def send(rows: list, timeout: float) -> None:
    """Publishes the rows in one call and marks them published. When Pub/Sub rejects the call,
    each row is tried alone, so only a row it won't take is counted against. Any other failure
    (an outage) raises and counts against no row."""
    messages = [
        pubsub.message(row.event_type, row.data, str(row.id), row.created_at) for row in rows
    ]

    try:
        await pubsub.publish_batch(messages, timeout)
    except Exception as error:
        if not rejected(error):
            raise

        if len(rows) == 1:
            count_rejection(rows[0], error)

            return

        for row in rows:
            await send([row], timeout)

        return

    now = datetime.now(UTC)

    for row in rows:
        row.published_at = now


async def flush_batch(
    sessionmaker, model, ids: list[uuid.UUID] | None, timeout: float
) -> tuple[int, int]:
    """Publishes one batch of waiting events, oldest first (with `ids`, only those), and returns
    how many it published and how many it took. Two runs never take the same row (SKIP LOCKED),
    and a row is locked only for its batch's one call. Parked rows are left out. A failure keeps
    the rest for the next run."""
    query = (
        select(model)
        .where(model.published_at.is_(None), model.attempts < OUTBOX_MAX_ATTEMPTS)
        .order_by(model.created_at)
        .limit(OUTBOX_BATCH)
        .with_for_update(skip_locked=True)
    )

    if ids is not None:
        query = query.where(model.id.in_(ids))

    async with sessionmaker() as session:
        rows = list(await session.scalars(query))

        try:
            if rows:
                await send(rows, timeout)
        finally:
            await session.commit()

    return sum(row.published_at is not None for row in rows), len(rows)


async def delete_old(sessionmaker, model) -> None:
    """Deletes events published more than OUTBOX_KEEP_DAYS ago, a batch at a time, and parked
    events saved that long ago: no flush sends those again, and their data (emails, reports)
    must not outlive the retention."""
    before = datetime.now(UTC) - timedelta(days=OUTBOX_KEEP_DAYS)
    await delete_in_batches(sessionmaker, model, model.published_at < before)
    parked = await delete_in_batches(
        sessionmaker,
        model,
        model.published_at.is_(None),
        model.attempts >= OUTBOX_MAX_ATTEMPTS,
        model.created_at < before,
    )

    if parked:
        logger.warning(
            "Deleted %s parked outbox events older than %s days", parked, OUTBOX_KEEP_DAYS
        )


async def flush(
    sessionmaker, model, ids: list[uuid.UUID] | None = None, timeout: float = HTTP_TIMEOUT_SECONDS
) -> int:
    """Publishes waiting events and returns how many; with `ids`, only those, in one batch. The
    scheduled flush (no `ids`) sends batch after batch until none wait, a batch has a row Pub/Sub
    rejected (it waits for the next run), or OUTBOX_FLUSH_SECONDS have passed; then it deletes
    old published and parked rows."""
    if ids is not None:
        published, _ = await flush_batch(sessionmaker, model, ids, timeout)

        return published

    deadline = time.monotonic() + OUTBOX_FLUSH_SECONDS
    total = 0

    try:
        while True:
            published, taken = await flush_batch(sessionmaker, model, None, timeout)
            total += published

            if taken < OUTBOX_BATCH or published < taken or time.monotonic() >= deadline:
                return total
    finally:
        await delete_old(sessionmaker, model)


async def flush_quietly(sessionmaker, model) -> None:
    """Right after a change: publishes the events this request saved, at once and with a short
    timeout. A failure is only logged, as the scheduled flush sends them a minute later."""
    saved = saved_ids.get()

    if not saved:
        return

    ids = list(saved)
    saved.clear()

    try:
        await flush(sessionmaker, model, ids, PUBLISH_IN_REQUEST_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Couldn't publish waiting events; the scheduled flush will")
