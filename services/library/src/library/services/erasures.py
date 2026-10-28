import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import status

from library.constants.accounts import (
    ERASURE_BATCH,
    ERASURE_KEEP_DAYS,
    ERASURE_RUN_SECONDS,
)
from library.core.db import Session
from library.integrations import accounts as services
from library.models.erasures import Erasure
from library.repositories import erasures
from library.services.accounts import delete_data

logger = logging.getLogger(__name__)


async def replay() -> int:
    """Runs the deletions of the last ERASURE_KEEP_DAYS again in every service, safe to repeat:
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


async def erase_again(erasure: Erasure) -> None:
    """One account's deletion run again in every service at once, then in library."""
    results = await asyncio.gather(
        *(
            services.delete_user(service, erasure.user_id, erasure.email)
            for service in services.services()
        ),
        return_exceptions=True,
    )

    for service, result in zip(services.services(), results, strict=True):
        if not isinstance(result, BaseException):
            continue

        # A company the restore gave back others' members: left to support, logged.
        refused = isinstance(result, httpx.HTTPStatusError) and (
            result.response.status_code == status.HTTP_409_CONFLICT
        )

        if not refused:
            raise result

        logger.error("Erasure of account %s refused by %s", erasure.user_id, service)

    await delete_data(erasure.user_id)
