import logging
import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events.notifications import NotificationKind

from library.constants.quality import FLAG_RESEND_AFTER_HOURS, MAX_FLAG_RESENDS, QualityFlag
from library.helpers.notifications import question_notification
from library.helpers.quality import flag_for, no_separation, too_slow
from library.integrations import generation
from library.repositories import preparations, quality
from library.services import outbox

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
    current = await quality.current_flag(question_id)

    if current == QualityFlag.WRONG_KEY:
        return

    # Marked twice at once, only one is sent.
    if await quality.change_flag(question_id, current, QualityFlag.WRONG_KEY):
        await send_to_verifier(question_id, QualityFlag.WRONG_KEY)


async def review(question_id: uuid.UUID) -> None:
    """Flags a question from its answers and feedback, and sends a new flag to the verifier.

    Never raises: a failed review is repeated by the question's next feedback, finished topic,
    or answer once it has MIN_ANSWERS.
    """
    try:
        found = await quality.load(question_id)

        if found is None:
            return

        question, stats, reports, likes, dislikes = found

        if stats is not None and stats.kept:
            return

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
            return

        # The owner hears only of a newly flagged question, not of a flag that changes.
        notice = None

        if flag is not None and previous is None:
            question_set = await preparations.get_for_question(question_id)
            topic = await preparations.topic_of_question(question_id)
            notice = question_notification(question_set, topic, NotificationKind.QUESTION_FLAGGED)

        # A flag cleared needs no check. A review of the same question at the same moment (an
        # answer and its finished topic) reads the same flag: only one of them changes it.
        if flag is None:
            await quality.save_flag(question_id, None)

            return

        # Saved before the verifier hears of it, so the verifier finds the flag it acts on.
        if not await quality.change_flag(question_id, previous, flag, notice):
            return

        if notice is not None:
            await outbox.flush_quietly()

        await send_to_verifier(question_id, flag)
    except Exception:
        logger.exception("Couldn't review question %s", question_id)


async def resend_stale_flags() -> int:
    """Daily: flags the verifier hasn't acted on for FLAG_RESEND_AFTER_HOURS go to it again, so
    a lost job doesn't leave a question flagged for good. How many were sent."""
    before = datetime.now(UTC) - timedelta(hours=FLAG_RESEND_AFTER_HOURS)
    stale = await quality.take_stale_flags(before, MAX_FLAG_RESENDS)

    for question_id, flag in stale:
        await send_to_verifier(question_id, flag)

    return len(stale)
