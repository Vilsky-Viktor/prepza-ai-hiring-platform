from uuid import UUID

from fastapi import APIRouter, status

from library.api.dependencies import ServiceCaller
from library.core.db import Session
from library.repositories import feedback
from library.schemas.feedback import (
    InternalRatingIn,
    InternalReportIn,
    MyReportOut,
    QuestionRatingOut,
)
from library.services import question_feedback

router = APIRouter(prefix="/internal/questions", tags=["internal"])


@router.get("/{question_id}/rating")
async def get_rating(question_id: UUID, user_id: str, caller: ServiceCaller) -> QuestionRatingOut:
    """For callers that already checked the user may see this question, e.g. a candidate."""
    async with Session() as session:
        return QuestionRatingOut(
            value=await feedback.my_question_rating(session, question_id, user_id)
        )


@router.put("/{question_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
async def rate(question_id: UUID, body: InternalRatingIn, caller: ServiceCaller) -> None:
    await question_feedback.rate(question_id, body.user_id, body.value)


@router.get("/{question_id}/reports/mine")
async def my_report(question_id: UUID, user_id: str, caller: ServiceCaller) -> MyReportOut:
    async with Session() as session:
        return MyReportOut(reported=await feedback.has_reported(session, question_id, user_id))


@router.post("/{question_id}/reports", status_code=status.HTTP_201_CREATED)
async def report(question_id: UUID, body: InternalReportIn, caller: ServiceCaller) -> None:
    """One report per user and question, whatever its revision. One already made is refused
    before it's counted; the count is against floods (with Redis down, not counted)."""
    await question_feedback.report(question_id, body.user_id, body.reason, body.comment)
