import time
import uuid

from fastapi import HTTPException, status
from prepza_common.config.constants import RETRY_AFTER
from prepza_common.events.notifications import NotificationKind

from library.constants.quality import COPY_FIX_BATCH, COPY_FIX_SECONDS
from library.core.db import Session
from library.repositories import copy_fixes
from library.services.notices import tell_owner


async def fix_copies(data: dict) -> None:
    """question.fixed: the bank question's copies that still hold its old content get the new
    one, batch after batch, each batch one save with its companies' notifications. Past
    COPY_FIX_SECONDS it answers 503, so Pub/Sub sends the event again and the next push goes on
    with the copies still left; safe to repeat and in any order, as each copy gets the
    original's current content."""
    question_id = uuid.UUID(data["question_id"])
    stop_at = time.monotonic() + COPY_FIX_SECONDS

    while await fix_batch(question_id, data["text"], data["options"]) == COPY_FIX_BATCH:
        if time.monotonic() >= stop_at:
            # Not done yet: Pub/Sub brings the event back for the copies left.
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, headers={RETRY_AFTER: "10"})


async def fix_batch(question_id: uuid.UUID, old_text: str, old_options: list[dict]) -> int:
    """One batch of copies fixed, each company told; how many."""
    async with Session.begin() as session:
        copies = await copy_fixes.fix_copies(session, question_id, old_text, old_options)

        for copy_id in copies:
            await tell_owner(session, copy_id, NotificationKind.QUESTION_FIXED)

    return len(copies)
