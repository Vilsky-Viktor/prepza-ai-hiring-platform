from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.db.paging import PageParams

from companies.integrations import library
from companies.models.interviews import Interview
from companies.schemas.interviews import QuestionText, ReportOut, TopicLimitIn
from companies.services import interview_changes, question_steps
from companies.services.interview_access import interview_for

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
    """How many of the topic's questions each candidate gets; 0 leaves the topic out. 422 over
    the topic's number of questions, for the last topic with questions, and over 60 questions
    per candidate over all topics (`too_many_questions`): lower another topic first."""
    interview = await generated_interview(user, interview_id, editor=True)
    await interview_changes.set_topic_limit(interview, topic_id, body.limit, user.uid)


@router.post("/{interview_id}/questions/{question_id}/regenerate")
async def regenerate_question(interview_id: UUID, question_id: UUID, user: CurrentUser) -> dict:
    interview = await generated_interview(user, interview_id, editor=True)

    return await question_steps.regenerate(interview, question_id, user.uid)


@router.post(
    "/{interview_id}/questions/{question_id}/wrong", status_code=status.HTTP_204_NO_CONTENT
)
async def mark_wrong(interview_id: UUID, question_id: UUID, user: CurrentUser) -> None:
    """One click: the marked answer is wrong. The verifier checks it and fixes or replaces it."""
    interview = await generated_interview(user, interview_id, editor=True)
    await question_steps.mark_wrong(interview, question_id, user.uid)


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
