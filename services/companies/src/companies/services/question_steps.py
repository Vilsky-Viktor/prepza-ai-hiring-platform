"""An owner or admin's steps on an interview's questions, done by generation and library and
recorded in the action log once they answer."""

from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.events.audit_actions import AuditAction
from prepza_common.http.http import passed_on
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit

from companies.integrations import billing, library
from companies.integrations import generation as generation_api
from companies.integrations.redis import get_redis
from companies.models.interviews import Interview
from companies.services import audit_records


async def regenerate(interview: Interview, question_id: UUID, user_id: str) -> dict:
    await refuse_if_paused(get_redis(), "question_regeneration", interview.company_id, user_id)
    response = await generation_api.regenerate_question(
        question_id, interview.set_id, user_id, await billing.company_paid(interview.company_id)
    )

    question = passed_on(response).json()
    await audit_records.record_interview(interview, user_id, AuditAction.QUESTIONS_REGENERATED)

    return question


async def mark_wrong(interview: Interview, question_id: UUID, user_id: str) -> None:
    """The marked answer is wrong: the verifier checks it and fixes or replaces it."""
    context = await library.get_question_context(question_id)

    if context is None or str(context["set_id"]) != str(interview.set_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    # Each mark starts the AI verifier: a company can't use up everyone's day of it.
    key = f"rate:wrong-marks:{interview.company_id}"
    await hit(get_redis(), key, "WRONG_MARKS_PER_COMPANY_DAY", company_id=interview.company_id)
    await library.mark_wrong(question_id)
    await audit_records.record_interview(interview, user_id, AuditAction.ANSWER_KEY_REPORTED)
