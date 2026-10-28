import time
import uuid

from fastapi import HTTPException, status
from prepza_common.config.constants import RETRY_AFTER

from library.constants.quality import COPY_FIX_BATCH, COPY_FIX_SECONDS
from library.repositories import copy_fixes


async def fix_copies(data: dict) -> None:
    """question.fixed: the bank question's copies that still hold its old content get the new
    one, batch after batch. Past COPY_FIX_SECONDS it answers 503, so Pub/Sub sends the event again
    and the next push goes on with the copies still left; safe to repeat and in any order, as
    each copy gets the original's current content."""
    question_id = uuid.UUID(data["question_id"])
    stop_at = time.monotonic() + COPY_FIX_SECONDS

    while await copy_fixes.fix_copies(question_id, data["text"], data["options"]) == COPY_FIX_BATCH:
        if time.monotonic() >= stop_at:
            # Not done yet: Pub/Sub brings the event back for the copies left.
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, headers={RETRY_AFTER: "10"})
