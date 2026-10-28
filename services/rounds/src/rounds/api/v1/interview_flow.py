from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth.auth import CurrentUser

from rounds.schemas.interview_flow import InterviewStep
from rounds.services import interview_flow
from rounds.services.session_access import get_owned_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/{session_id}/step")
async def next_step(session_id: UUID, user: CurrentUser) -> InterviewStep:
    """Opens the candidate's interview, or moves it on after an answer or a time-out: the
    server decides which section and question come next, and when the interview is done."""
    row = await get_owned_session(session_id, user)

    return await interview_flow.interview_step(row, user)


@router.post("/{session_id}/finish-interview")
async def finish_interview(session_id: UUID, user: CurrentUser) -> InterviewStep:
    row = await get_owned_session(session_id, user)

    return await interview_flow.finish_interview(row, user)
