from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth.auth import CurrentUser

from rounds.schemas.rounds import AnswerCreate
from rounds.schemas.sessions import SessionAnswerResult, SignalIn
from rounds.services import signals, voice_deadline
from rounds.services.session_access import get_owned_session
from rounds.services.session_answers import submit_session_answer

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/{session_id}/signals", status_code=204)
async def add_signal(session_id: UUID, body: SignalIn, user: CurrentUser) -> None:
    """The candidate's browser reports leaving the page or copying, saved with the question on
    screen so the scorecard can show where it happened; and coming back, with how long the leave
    lasted, which decides whether it counts (helpers/integrity.py). Only in a company's
    interview: a practice round or a preview records none, as no one assesses them."""
    await signals.record(session_id, body, user)


@router.post("/{session_id}/answers", status_code=201)
async def answer_question(
    session_id: UUID, body: AnswerCreate, user: CurrentUser
) -> SessionAnswerResult:
    # An answer sent just before the clock ran out still counts, and a spoken one the service
    # received in time a little longer, while it's understood.
    grace = await voice_deadline.answer_grace(session_id, body.question_id)
    row = await get_owned_session(session_id, user, grace)

    return await submit_session_answer(row, body)
