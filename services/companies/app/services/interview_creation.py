import httpx
from fastapi import HTTPException, status
from prepza_common.events.analytics import track
from prepza_common.events.audit_actions import AuditAction
from prepza_common.http.http import passed_on
from prepza_common.limits.limit_list import LIMITS
from prepza_common.limits.limits import at_most, limit, question_seconds
from prepza_common.limits.rate_limit import counted, hit

from app.constants import error_codes
from app.constants.generation import GENERATION_REFUSALS
from app.constants.interviews import UNKNOWN_LEVEL
from app.constants.invites import (
    TOO_MANY_INTERVIEWS,
    TOO_MANY_INTERVIEWS_UNPAID,
    TOO_MANY_WITHOUT_CANDIDATES,
    TOO_MANY_WITHOUT_CANDIDATES_UNPAID,
)
from app.core.exceptions import OverLimit
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

    quota = (
        "MAX_INTERVIEWS_WITHOUT_CANDIDATES" if paid else "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID"
    )

    async def refuse_over(count: int) -> None:
        try:
            await at_most(
                redis,
                quota,
                count,
                # Waiting won't free one, inviting a candidate will: a quota, not a rate limit.
                status.HTTP_409_CONFLICT,
                TOO_MANY_WITHOUT_CANDIDATES if paid else TOO_MANY_WITHOUT_CANDIDATES_UNPAID,
                **who,
                code=error_codes.INTERVIEW_QUOTA_REACHED,
            )
        except HTTPException:
            await track("limit_hit", which="interviews_without_candidates", **who)
            raise

    # Checked first, so a refused attempt doesn't count towards the day's limit.
    await refuse_over(await interviews.without_candidates(company.id))

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
    # Counted again under a lock as it's saved: another made meanwhile may have taken the last
    # place. No lock is held across the generation call; the refused one's generation stops.
    try:
        interview = await interviews.create(
            company.id, created["id"], created["language"], seconds, await limit(redis, quota)
        )
    except OverLimit as over:
        await generation_api.cancel(created["id"], company.id)
        await counted(redis, daily_key, -1, LIMITS[daily].window)
        await refuse_over(over.count)
        raise
    await audit.record_interview(interview, user_id, AuditAction.INTERVIEW_CREATED, via)

    return await interview_out(interview)
