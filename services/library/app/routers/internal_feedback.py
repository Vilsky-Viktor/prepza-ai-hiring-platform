from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.rate_limit import hit_or_skip

from app.integrations.redis import get_redis
from app.schemas.feedback import (
    InternalRatingIn,
    InternalReportIn,
    MyReportOut,
    QuestionRatingOut,
)
from app.service_auth import ServiceCaller
from app.services.quality import review
from app.storage import feedback

router = APIRouter(prefix="/internal/questions", tags=["internal"])


@router.get("/{question_id}/rating")
async def get_rating(question_id: UUID, user_id: str, caller: ServiceCaller) -> QuestionRatingOut:
    """For callers that already checked the user may see this question, e.g. a candidate."""
    return QuestionRatingOut(value=await feedback.my_question_rating(question_id, user_id))


@router.put("/{question_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
async def rate(question_id: UUID, body: InternalRatingIn, caller: ServiceCaller) -> None:
    key = f"rate:ratings:{body.user_id}"
    await hit_or_skip(get_redis(), key, "RATINGS_PER_DAY", user_id=body.user_id)
    await feedback.rate_question(question_id, body.user_id, body.value)

    await review(question_id)


@router.get("/{question_id}/reports/mine")
async def my_report(question_id: UUID, user_id: str, caller: ServiceCaller) -> MyReportOut:
    return MyReportOut(reported=await feedback.has_reported(question_id, user_id))


@router.post("/{question_id}/reports", status_code=status.HTTP_201_CREATED)
async def report(question_id: UUID, body: InternalReportIn, caller: ServiceCaller) -> None:
    """One report per user and question, whatever its revision. One already made is refused
    before it's counted; the count is against floods (with Redis down, not counted)."""
    if await feedback.has_reported(question_id, body.user_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Already reported")

    key = f"rate:reports:{body.user_id}"
    await hit_or_skip(get_redis(), key, "REPORTS_PER_DAY", user_id=body.user_id)

    if not await feedback.report_question(question_id, body.user_id, body.reason, body.comment):
        raise HTTPException(status.HTTP_409_CONFLICT, "Already reported")

    await review(question_id)
