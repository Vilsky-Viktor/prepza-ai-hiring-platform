import logging
import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events.notifications import NotificationKind

from library.constants.quality import FLAG_RESEND_AFTER_HOURS, MAX_FLAG_RESENDS, QualityFlag
from library.core.db import Session
from library.helpers.quality import flag_for, no_separation, too_slow
from library.integrations import generation
from library.repositories import bank, quality
from library.services import outbox
from library.services.notices import owner_notice

logger = logging.getLogger(__name__)


async def send_to_verifier(question_id: uuid.UUID, flag: str) -> None:
    """Never raises: the flag is saved first, and resend_stale_flags sends it again later."""
    try:
        await generation.verify_question(question_id, flag)
    except Exception:
        logger.exception("Couldn't send question %s to the verifier", question_id)


async def mark_wrong(question_id: uuid.UUID) -> None:
    """The test's owner says the marked answer is wrong: flagged at once, and the verifier
    checks it and fixes or replaces the question, as for a flag from answers. Marking it again
    while that check waits changes nothing."""
    async with Session.begin() as session:
        current = await quality.current_flag(session, question_id)

        if current == QualityFlag.WRONG_KEY:
            return

        # Marked twice at once, only one is sent.
        changed = await quality.change_flag(session, question_id, current, QualityFlag.WRONG_KEY)

        if changed:
            await bank.leave(session, [question_id])

    if changed:
        await send_to_verifier(question_id, QualityFlag.WRONG_KEY)


async def keep(question_id: uuid.UUID) -> None:
    """The flag is wrong: the question is served again and isn't flagged until it changes."""
    async with Session.begin() as session:
        await quality.save_flag(session, question_id, None, kept=True)


async def review(question_id: uuid.UUID) -> None:
    """Flags a question from its answers and feedback, and sends a new flag to the verifier.

    Never raises: a failed review is repeated by the question's next feedback, finished topic,
    or answer once it has MIN_ANSWERS.
    """
    try:
        flagged = await save_review(question_id)

        if flagged is None:
            return

        flag, noticed = flagged

        if noticed:
            await outbox.flush_quietly()

        await send_to_verifier(question_id, flag)
    except Exception:
        logger.exception("Couldn't review question %s", question_id)


async def save_review(question_id: uuid.UUID) -> tuple[str, bool] | None:
    """Saves the flag the question's answers and feedback give it; the new flag and whether its
    owner is told, or None when nothing goes to the verifier."""
    async with Session.begin() as session:
        found = await quality.load(session, question_id)

        if found is None:
            return None

        question, stats, reports, likes, dislikes = found

        if stats is not None and stats.kept:
            return None

        flag = flag_for(
            question.options,
            stats.answers if stats else 0,
            stats.correct if stats else 0,
            stats.option_picks if stats else {},
            reports,
            likes,
            dislikes,
            stats is not None and (no_separation(stats) or too_slow(stats)),
        )
        previous = stats.flag if stats else None

        if flag == previous:
            return None

        # A flag cleared needs no check. A review of the same question at the same moment (an
        # answer and its finished topic) reads the same flag: only one of them changes it.
        if flag is None:
            await quality.save_flag(session, question_id, None)

            return None

        # The owner hears only of a newly flagged question, not of a flag that changes.
        notice = None

        if previous is None:
            notice = await owner_notice(session, question_id, NotificationKind.QUESTION_FLAGGED)

        # Saved before the verifier hears of it, so the verifier finds the flag it acts on.
        if not await quality.change_flag(session, question_id, previous, flag, notice):
            return None

        # Flagged, it leaves the shared bank for everyone, with what it's a copy of.
        await bank.leave(session, [question_id])

        return flag, notice is not None


async def resend_stale_flags() -> int:
    """Daily: flags the verifier hasn't acted on for FLAG_RESEND_AFTER_HOURS go to it again, so
    a lost job doesn't leave a question flagged for good. How many were sent."""
    before = datetime.now(UTC) - timedelta(hours=FLAG_RESEND_AFTER_HOURS)

    async with Session.begin() as session:
        stale = await quality.take_stale_flags(session, before, MAX_FLAG_RESENDS)

    for question_id, flag in stale:
        await send_to_verifier(question_id, flag)

    return len(stale)
