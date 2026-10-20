from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth import CurrentUser
from prepza_common.rate_limit import hit_or_skip

from app.constants.integrity import IntegritySignal
from app.constants.rounds import TIME_GRACE_SECONDS, RoundStatus
from app.helpers.sessions import next_session_question
from app.integrations.redis import get_redis
from app.schemas.rounds import AnswerCreate
from app.schemas.sessions import SessionAnswerResult, SignalIn
from app.services.session_access import get_own_session, get_owned_session
from app.services.session_answers import submit_session_answer
from app.storage import signals

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/{session_id}/signals", status_code=204)
async def add_signal(session_id: UUID, body: SignalIn, user: CurrentUser) -> None:
    """The candidate's browser reports leaving the page or copying, saved with the question on
    screen so the scorecard can show where it happened; and coming back, with how long the leave
    lasted, which decides whether it counts (helpers/integrity.py). Only in a company's
    interview: a practice round or a preview records none, as no one assesses them."""
    row = await get_own_session(session_id, user)

    if row.status != RoundStatus.IN_PROGRESS or row.practice or row.preview:
        return

    # Against flooding only (a question keeps at most MAX_SIGNALS_PER_QUESTION anyway): with
    # Redis down the signal is still saved rather than lost.
    await hit_or_skip(get_redis(), f"rate:signals:{row.id}", "SIGNALS_PER_MINUTE", user_id=user.uid)

    if body.kind == IntegritySignal.TAB_RETURN:
        if body.seconds is not None:
            await signals.set_away(row.id, body.seconds)

        return

    question = next_session_question(row) if row.question_shown_at else None
    await signals.add_signal(row.id, question.question_id if question else None, body.kind)


@router.post("/{session_id}/answers", status_code=201)
async def answer_question(
    session_id: UUID, body: AnswerCreate, user: CurrentUser
) -> SessionAnswerResult:
    # An answer sent just before the clock ran out still counts.
    row = await get_owned_session(session_id, user, TIME_GRACE_SECONDS)

    return await submit_session_answer(row, body)
