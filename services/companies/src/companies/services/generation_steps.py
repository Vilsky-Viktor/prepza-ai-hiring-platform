"""An owner or admin's steps in an interview's generation: approving its topics and running it
again. Both are AI work, so the pause and the unpaid AI cap refuse them."""

from fastapi import Request
from prepza_common.ai import ai_cap
from prepza_common.auth.human_check import require_human
from prepza_common.events.audit_actions import AuditAction
from prepza_common.http.http import passed_on
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit

from companies.config import settings
from companies.constants.generation import GENERATION_REFUSALS
from companies.core.db import Session
from companies.integrations import billing
from companies.integrations import generation as generation_api
from companies.integrations.redis import get_redis
from companies.models.interviews import Interview
from companies.repositories import interview_generations
from companies.services import audit_records


async def review(
    interview: Interview, topics: dict, user_id: str, via: str | None, request: Request
) -> dict:
    """Approved topics resume the generation, so a pause refuses it. A company that never paid
    shows it's a person on the site first, as generating costs (the assistant and AI apps, with
    no browser, can't be asked), and is refused once today's unpaid AI spend reached its cap."""
    company_id = interview.company_id
    await refuse_if_paused(get_redis(), "interview_generation", company_id, user_id)

    if not await billing.company_paid(company_id):
        if via is None and settings.turnstile_secret_key:
            await require_human(request, settings.turnstile_secret_key)

        await ai_cap.refuse_if_capped(get_redis(), company_id, user_id)

    response = await generation_api.review(interview.generation_id, company_id, topics)
    reviewed = passed_on(response, GENERATION_REFUSALS).json()
    await audit_records.record_interview(interview, user_id, AuditAction.TOPICS_APPROVED, via)

    return reviewed


async def retry(interview: Interview, user_id: str) -> dict:
    """Runs the generation again, so it's refused as a review is (without the person check)."""
    company_id = interview.company_id
    await refuse_if_paused(get_redis(), "interview_generation", company_id, user_id)

    if not await billing.company_paid(company_id):
        await ai_cap.refuse_if_capped(get_redis(), company_id, user_id)

    # A run again is AI work as the first was.
    key = f"rate:generation-retries:{company_id}"
    await hit(get_redis(), key, "GENERATION_RETRIES_PER_COMPANY_DAY", company_id=company_id)
    retried = passed_on(
        await generation_api.retry(interview.generation_id, company_id), GENERATION_REFUSALS
    ).json()

    # Generating again: its lists stop showing the failure.
    async with Session.begin() as session:
        await interview_generations.set_generation_failed(session, interview.id, False)

    return retried
