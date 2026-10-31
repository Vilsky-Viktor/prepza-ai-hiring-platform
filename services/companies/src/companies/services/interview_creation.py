import httpx
from fastapi import HTTPException, status
from testee_common.events.analytics import track
from testee_common.events.audit_actions import AuditAction
from testee_common.http.http import passed_on
from testee_common.limits.limit_list import LIMITS
from testee_common.limits.limits import at_most, limit, question_seconds
from testee_common.limits.pause import refuse_if_paused
from testee_common.limits.rate_limit import counted, hit, hit_or_skip

from companies.constants import error_codes
from companies.constants.audit import VIA_API
from companies.constants.generation import GENERATION_REFUSALS
from companies.constants.interviews import UNKNOWN_LEVEL
from companies.constants.invites import (
    TOO_MANY_INTERVIEWS,
    TOO_MANY_INTERVIEWS_UNPAID,
    TOO_MANY_WITHOUT_CANDIDATES,
    TOO_MANY_WITHOUT_CANDIDATES_UNPAID,
)
from companies.core.db import Session
from companies.core.exceptions import OverLimit
from companies.integrations import billing, library
from companies.integrations import generation as generation_api
from companies.integrations.redis import get_redis
from companies.models.companies import Company
from companies.repositories import audit, companies, interviews
from companies.schemas.interviews import InterviewOut
from companies.services.interview_views import interview_out


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
    async with Session() as session:
        waiting = await interviews.without_candidates(session, company.id)

    await refuse_over(waiting)

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
    most = await limit(redis, quota)
    # Counted again under a lock as it's saved, with its line in the action log: another made
    # meanwhile may have taken the last place. No lock is held across the generation call; the
    # refused one's generation stops.
    try:
        async with Session.begin() as session:
            interview = await interviews.create(
                session, company.id, created["id"], created["language"], seconds, most
            )
            await audit.record_interview(
                session, interview, user_id, AuditAction.INTERVIEW_CREATED, via
            )
    except OverLimit as over:
        await generation_api.cancel(created["id"], company.id)
        await counted(redis, daily_key, -1, LIMITS[daily].window)
        await refuse_over(over.count)
        raise

    return await interview_out(interview)


async def create_from_template(company: Company, user_id: str, template_id) -> InterviewOut:
    """A test copied from a template: free and ready at once, so no generation limits apply;
    saved with its line in the action log."""
    redis = get_redis()
    who = {"company_id": company.id, "user_id": user_id}
    await hit_or_skip(
        redis, f"rate:template-copies:{company.id}", "TEMPLATE_COPIES_PER_HOUR", **who
    )
    copy = await library.copy_template(template_id, company.id)

    if copy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    seconds = await question_seconds(redis, copy["level"])

    async with Session.begin() as session:
        interview = await interviews.create_from_template(
            session, company.id, copy["id"], copy["title"], copy["language"], seconds
        )
        await audit.record_interview(
            session, interview, user_id, AuditAction.INTERVIEW_FROM_TEMPLATE
        )

    await track("interview_from_template", **who, set_id=copy["id"])
    # Ready at once: no generation to wait for.
    await track("test_ready", **who, how="template")

    return await interview_out(interview)


async def create_for_api(
    company_id, user_id: str, text: str, generate_in: str | None
) -> InterviewOut:
    """create, through the public API as `user_id`, the key itself (key_actor): refused during
    the emergency pause, 404 for a company that's gone."""
    await refuse_if_paused(get_redis(), "interview_generation", company_id, user_id)

    async with Session() as session:
        company = await companies.get(session, company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found")

    return await create(company, user_id, None, text, generate_in, VIA_API)
