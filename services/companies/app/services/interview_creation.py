import httpx
from fastapi import HTTPException, status
from prepza_common.analytics import track
from prepza_common.audit_actions import AuditAction
from prepza_common.http import passed_on
from prepza_common.limit_list import LIMITS
from prepza_common.limits import at_most, question_seconds
from prepza_common.rate_limit import counted, hit

from app.constants.interviews import GENERATION_REFUSALS, UNKNOWN_LEVEL
from app.constants.invites import (
    TOO_MANY_INTERVIEWS,
    TOO_MANY_INTERVIEWS_UNPAID,
    TOO_MANY_WITHOUT_CANDIDATES,
    TOO_MANY_WITHOUT_CANDIDATES_UNPAID,
)
from app.helpers.interviews import interview_out
from app.integrations import billing
from app.integrations import generation as generation_api
from app.integrations.redis import get_redis
from app.models.companies import Company
from app.schemas.interviews import InterviewOut
from app.storage import audit, interviews


async def create(
    company: Company,
    user_id: str,
    language: str | None,
    text: str,
    generate_in: str | None,
    via: str | None = None,
) -> InterviewOut:
    """Starts making an interview from a job description, as `user_id`, an owner or admin (on
    the site or through the API; each checks the pause first): refused past the company's
    interviews without candidates and past its interviews a day (fewer until it tops up)."""
    # A company that ever topped up gets more (the costs are covered by its candidates).
    paid = await billing.company_paid(company.id)
    redis = get_redis()
    who = {"company_id": company.id, "user_id": user_id}

    # Checked first, so a refused attempt doesn't count towards the day's limit.
    try:
        await at_most(
            redis,
            "MAX_INTERVIEWS_WITHOUT_CANDIDATES"
            if paid
            else "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID",
            await interviews.without_candidates(company.id),
            # Waiting won't free one, inviting a candidate will: a quota, not a rate limit.
            status.HTTP_409_CONFLICT,
            TOO_MANY_WITHOUT_CANDIDATES if paid else TOO_MANY_WITHOUT_CANDIDATES_UNPAID,
            **who,
        )
    except HTTPException:
        await track("limit_hit", which="interviews_without_candidates", **who)
        raise

    daily = "INTERVIEWS_PER_DAY" if paid else "INTERVIEWS_PER_DAY_UNPAID"
    daily_key = f"rate:interviews:{company.id}"

    try:
        await hit(
            redis,
            daily_key,
            daily,
            TOO_MANY_INTERVIEWS if paid else TOO_MANY_INTERVIEWS_UNPAID,
            **who,
        )
    except HTTPException:
        await track("limit_hit", user_id=user_id, company_id=company.id, which="interviews_a_day")
        raise

    try:
        created = await generation_api.create(
            text, company.id, user_id, language, generate_in, paid
        )
    except Exception as error:
        # Nothing was made: the attempt gives back its place in the day's count.
        await counted(redis, daily_key, -1, LIMITS[daily].window)

        if isinstance(error, httpx.HTTPStatusError):
            # Generation's own refusal (its limit per person, the day's AI budget), as it said it.
            passed_on(error.response, GENERATION_REFUSALS)

        raise

    # Generation picks the language from the job description, not from the recruiter's interface.
    seconds = await question_seconds(redis, UNKNOWN_LEVEL)
    interview = await interviews.create(company.id, created["id"], created["language"], seconds)
    await audit.record_interview(interview, user_id, AuditAction.INTERVIEW_CREATED, via)

    return await interview_out(interview)
