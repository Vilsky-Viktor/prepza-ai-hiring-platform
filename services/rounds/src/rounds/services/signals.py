from uuid import UUID

from prepza_common.auth.user import User
from prepza_common.limits.limits import limit
from prepza_common.limits.rate_limit import hit_or_skip

from rounds.constants.integrity import IntegritySignal
from rounds.constants.rounds import RoundStatus
from rounds.core.db import Session
from rounds.helpers.sessions import next_session_question
from rounds.integrations.redis import get_redis
from rounds.repositories import signals
from rounds.schemas.sessions import SignalIn
from rounds.services.session_access import get_own_session


async def record(session_id: UUID, body: SignalIn, user: User) -> None:
    """A page leave or a copy, saved with the question on screen so the scorecard can show where
    it happened; or a return, with how long the leave lasted, which decides whether it counts
    (helpers/integrity.py). Only in a company's interview: a practice round or a preview records
    none, as no one assesses them."""
    row = await get_own_session(session_id, user)

    if row.status != RoundStatus.IN_PROGRESS or row.practice or row.preview:
        return

    redis = get_redis()
    # Against flooding only (a question keeps at most MAX_SIGNALS_PER_QUESTION anyway): with
    # Redis down the signal is still saved rather than lost.
    await hit_or_skip(redis, f"rate:signals:{row.id}", "SIGNALS_PER_MINUTE", user_id=user.uid)

    if body.kind == IntegritySignal.TAB_RETURN:
        if body.seconds is not None:
            async with Session.begin() as session:
                await signals.set_away(session, row.id, body.seconds)

        return

    question = next_session_question(row) if row.question_shown_at else None
    # One already flags the candidate, more say nothing new.
    most = await limit(redis, "MAX_SIGNALS_PER_QUESTION")

    async with Session.begin() as session:
        await signals.add_signal(
            session, row.id, question.question_id if question else None, body.kind, most
        )
