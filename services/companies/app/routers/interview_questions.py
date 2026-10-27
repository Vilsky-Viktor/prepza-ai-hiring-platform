from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.db.paging import PageParams
from prepza_common.events.audit_actions import AuditAction
from prepza_common.http.http import passed_on
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit

from app.constants.interviews import NO_QUESTIONS_LEFT
from app.helpers.interviews import interview_questions
from app.integrations import billing, library
from app.integrations import generation as generation_api
from app.integrations.redis import get_redis
from app.models.interviews import Interview
from app.schemas.interviews import QuestionText, ReportOut, TopicLimitIn
from app.services.interview_access import interview_for
from app.storage import audit, interviews

router = APIRouter(prefix="/interviews", tags=["interviews"])


async def generated_interview(
    user: CurrentUser, interview_id: UUID, editor: bool = False
) -> Interview:
    """The user's interview (interview_for), only one whose questions are made."""
    interview, _, _ = await interview_for(user, interview_id, editor)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")

    return interview


@router.get("/{interview_id}/topics/{topic_id}/questions")
async def list_topic_questions(
    interview_id: UUID, topic_id: UUID, user: CurrentUser
) -> list[QuestionText]:
    interview = await generated_interview(user, interview_id)
    questions = await library.get_topic_questions(interview.set_id, topic_id)

    if questions is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")

    return [QuestionText(**question) for question in questions]


@router.put("/{interview_id}/topics/{topic_id}/limit", status_code=status.HTTP_204_NO_CONTENT)
async def set_topic_limit(
    interview_id: UUID, topic_id: UUID, body: TopicLimitIn, user: CurrentUser
) -> None:
    interview = await generated_interview(user, interview_id, editor=True)
    found = await library.get_set(interview.set_id) or {}
    topic = next(
        (item for item in found.get("topics", []) if str(item["id"]) == str(topic_id)), None
    )

    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")

    if body.limit > topic["question_count"]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"The topic has only {topic['question_count']} questions",
        )

    # Every candidate gets at least one question.
    def keeps_questions(limits: dict[str, int]) -> bool:
        return bool(interview_questions(found, limits))

    if not await interviews.set_topic_limit(interview.id, topic_id, body.limit, keeps_questions):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NO_QUESTIONS_LEFT)

    await audit.record_interview(interview, user.uid, AuditAction.INTERVIEW_SETTINGS_CHANGED)


@router.post("/{interview_id}/questions/{question_id}/regenerate")
async def regenerate_question(interview_id: UUID, question_id: UUID, user: CurrentUser) -> dict:
    interview = await generated_interview(user, interview_id, editor=True)
    await refuse_if_paused(get_redis(), "question_regeneration", interview.company_id, user.uid)
    response = await generation_api.regenerate_question(
        question_id, interview.set_id, user.uid, await billing.company_paid(interview.company_id)
    )

    question = passed_on(response).json()
    await audit.record_interview(interview, user.uid, AuditAction.QUESTIONS_REGENERATED)

    return question


@router.post(
    "/{interview_id}/questions/{question_id}/wrong", status_code=status.HTTP_204_NO_CONTENT
)
async def mark_wrong(interview_id: UUID, question_id: UUID, user: CurrentUser) -> None:
    """One click: the marked answer is wrong. The verifier checks it and fixes or replaces it."""
    interview = await generated_interview(user, interview_id, editor=True)
    context = await library.get_question_context(question_id)

    if context is None or str(context["set_id"]) != str(interview.set_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    # Each mark starts the AI verifier: a company can't use up everyone's day of it.
    key = f"rate:wrong-marks:{interview.company_id}"
    await hit(get_redis(), key, "WRONG_MARKS_PER_COMPANY_DAY", company_id=interview.company_id)
    await library.mark_wrong(question_id)
    await audit.record_interview(interview, user.uid, AuditAction.ANSWER_KEY_REPORTED)


@router.get("/{interview_id}/questions/{question_id}/reports")
async def list_question_reports(
    interview_id: UUID, question_id: UUID, user: CurrentUser, page: PageParams
) -> list[ReportOut]:
    """Candidates' reports on a question, read where it's fixed: owners and admins."""
    interview = await generated_interview(user, interview_id, editor=True)
    reports = await library.get_question_reports(interview.set_id, question_id, page)

    if reports is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    return [ReportOut(**report) for report in reports]
