from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Response, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.http.http import passed_on

from app.helpers.rounds import find_question
from app.integrations import feedback
from app.schemas.feedback import RatingIn, ReportIn
from app.services.session_access import get_own_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def require_session_question(session_id: UUID, question_id: UUID, user: CurrentUser) -> None:
    """Candidates rate and report only questions of their own interview session."""
    row = await get_own_session(session_id, user)

    if find_question(row, str(question_id)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")


def passed_through(response: httpx.Response) -> Response:
    """Keeps the library's 409 (already rated or reported), validation errors and 429 (its daily
    ratings or reports limit) for the client."""
    kept = {
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        status.HTTP_429_TOO_MANY_REQUESTS,
    }
    passed_on(response, kept)

    return Response(response.content, response.status_code, media_type="application/json")


@router.get("/{session_id}/questions/{question_id}/rating")
async def get_rating(session_id: UUID, question_id: UUID, user: CurrentUser) -> Response:
    await require_session_question(session_id, question_id, user)

    return passed_through(await feedback.get_rating(question_id, user.uid))


@router.put("/{session_id}/questions/{question_id}/rating")
async def rate(session_id: UUID, question_id: UUID, body: RatingIn, user: CurrentUser) -> Response:
    await require_session_question(session_id, question_id, user)

    return passed_through(await feedback.rate(question_id, user.uid, body.value))


@router.get("/{session_id}/questions/{question_id}/reports/mine")
async def my_report(session_id: UUID, question_id: UUID, user: CurrentUser) -> Response:
    await require_session_question(session_id, question_id, user)

    return passed_through(await feedback.my_report(question_id, user.uid))


@router.post("/{session_id}/questions/{question_id}/reports")
async def report(
    session_id: UUID, question_id: UUID, body: ReportIn, user: CurrentUser
) -> Response:
    await require_session_question(session_id, question_id, user)

    return passed_through(await feedback.report(question_id, user.uid, body.reason, body.comment))
