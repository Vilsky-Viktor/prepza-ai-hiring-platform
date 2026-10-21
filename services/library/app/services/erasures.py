import logging
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import status

from app.constants.accounts import ERASURE_KEEP_DAYS
from app.integrations import accounts as services
from app.storage import accounts, erasures

logger = logging.getLogger(__name__)


async def replay() -> int:
    """Runs the deletions of the last ERASURE_KEEP_DAYS again in every service, safe to repeat:
    after a database is restored or cloned from a backup, nobody deleted since comes back. Then
    forgets older ones. Returns how many it ran. The sign-ins were deleted in Firebase, which
    no restore brings back."""
    now = datetime.now(UTC)
    before = now - timedelta(days=ERASURE_KEEP_DAYS)
    await erasures.forget(before)
    erased = await erasures.since(before)

    for erasure in erased:
        for service in services.services():
            try:
                await services.delete_user(service, erasure.user_id, erasure.email)
            except httpx.HTTPStatusError as error:
                # A company the restore gave back others' members: left to support, logged.
                if error.response.status_code != status.HTTP_409_CONFLICT:
                    raise

                logger.error("Erasure of account %s refused by %s", erasure.user_id, service)

        await accounts.delete_user(erasure.user_id)

    return len(erased)
