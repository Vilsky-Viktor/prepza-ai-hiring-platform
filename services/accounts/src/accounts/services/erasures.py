import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import status
from prepza_common.events.deletions import USER_DELETED, UserDeleted

from accounts.constants.accounts import (
    ERASURE_BATCH,
    ERASURE_KEEP_DAYS,
    ERASURE_RUN_SECONDS,
)
from accounts.core.db import Session
from accounts.integrations import services
from accounts.models.erasures import Erasure
from accounts.repositories import erasures, outbox, user_data
from accounts.services import outbox as outbox_service

logger = logging.getLogger(__name__)


async def replay() -> int:
    """Runs the deletions of the last ERASURE_KEEP_DAYS again everywhere, safe to repeat:
    after a database is restored or cloned from a backup, nobody deleted since comes back. Then
    forgets older ones. Newest first, a batch at once, until ERASURE_RUN_SECONDS into the run;
    a run stopped for time leaves the rest to the next. Returns how many it ran. The sign-ins
    were deleted in Firebase, which no restore brings back."""
    now = datetime.now(UTC)
    before = now - timedelta(days=ERASURE_KEEP_DAYS)
    await erasures.forget(Session, before)
    stop_at = time.monotonic() + ERASURE_RUN_SECONDS
    below = None
    count = 0

    while True:
        async with Session() as session:
            batch = await erasures.page(session, before, below, ERASURE_BATCH)

        results = await asyncio.gather(
            *(erase_again(erasure) for erasure in batch), return_exceptions=True
        )
        failed = [result for result in results if isinstance(result, BaseException)]

        if failed:
            raise failed[0]

        count += len(batch)

        if len(batch) < ERASURE_BATCH:
            return count

        if time.monotonic() >= stop_at:
            logger.warning("Ran %d recent account deletions again; the rest in the next run", count)

            return count

        below = (batch[-1].erased_at, batch[-1].user_id)


async def erase(user_id: str, email: str) -> None:
    """In one save: what accounts keeps under the user goes, with the note that runs the
    deletion again after a restore (kept from the first time) and the `user.deleted` event every
    other holder deletes its part by. Neither is kept without the others. The event is published
    at once; when that fails, the outbox's flush sends it within a minute."""
    async with Session.begin() as session:
        await user_data.delete_user(session, user_id)
        await erasures.record(session, user_id, email)
        outbox.add(session, USER_DELETED, UserDeleted(user_id=user_id, email=email).model_dump())

    await outbox_service.flush_quietly()


async def erase_again(erasure: Erasure) -> None:
    """One account's deletion run again: in companies, then everywhere else by the event."""
    try:
        await services.delete_in_companies(erasure.user_id, erasure.email)
    except httpx.HTTPStatusError as error:
        if error.response.status_code != status.HTTP_409_CONFLICT:
            raise

        # A company the restore gave back others' members: left to support, logged.
        logger.error("Erasure of account %s refused by companies", erasure.user_id)

    await erase(erasure.user_id, erasure.email)
