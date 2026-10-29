import asyncio
import logging

import httpx

from companies.constants.menu_counts import MENU_COUNT_TIMEOUT_SECONDS
from companies.core.db import Session
from companies.integrations import active_counts, billing
from companies.models.companies import Company
from companies.repositories import interviews
from companies.schemas.companies import MenuCountsOut

logger = logging.getLogger(__name__)


async def menu_counts(company: Company, user_id: str) -> MenuCountsOut:
    """What the company's menu shows beside its pages: its interviews, its team as the Team page
    lists it (members and pending invites), its working integrations and its referral rewards.
    A part another service couldn't give in time is None, and the menu shows it without."""
    async with Session() as session:
        totals = await interviews.counts(session, [company.id])

    integrations, referrals = await asyncio.gather(
        integration_count(company, user_id), referral_count(company)
    )

    return MenuCountsOut(
        interviews=totals.get(company.id, 0),
        members=len(company.members),
        integrations=integrations,
        referrals=referrals,
    )


async def integration_count(company: Company, user_id: str) -> int | None:
    """The company's working integrations, as its integrations page shows them: ATSs, Slack, API
    keys and web hooks, and the AI apps the user connected while the company allows them. A
    service that didn't answer adds none; None when no service answered."""
    calls = [
        active_counts.ats_count(company.id),
        active_counts.slack_count(company.id),
        active_counts.api_count(company.id),
    ]

    if company.ai_apps_off_at is None:
        calls.append(active_counts.ai_apps_count(user_id, company.id))

    answered = [count for count in await asyncio.gather(*calls) if count is not None]

    return sum(answered) if answered else None


async def referral_count(company: Company) -> int | None:
    """How many companies the company's referral link earned it a reward for, as its referrals
    page counts them; None when billing didn't answer in time."""
    try:
        found = await asyncio.wait_for(
            billing.company_referral(company.id), MENU_COUNT_TIMEOUT_SECONDS
        )
    except (httpx.HTTPError, TimeoutError):
        logger.warning("No referral count from billing for company %s", company.id)

        return None

    return found["rewarded"]
