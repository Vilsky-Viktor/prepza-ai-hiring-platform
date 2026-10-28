"""The user's companies as the site lists them."""

from companies.constants.roles import EDITORS
from companies.core.db import Session
from companies.core.security import REQUEST_COMPANY
from companies.integrations import billing
from companies.models.companies import Company
from companies.repositories import companies, interviews


async def listed(user_id: str, offset: int, limit: int) -> list[tuple[Company, int]]:
    """The user's companies, each with its number of interviews; for an AI agent signed in with
    an API key, the key's only."""
    async with Session() as session:
        rows = await companies.list_for_user(
            session, user_id, offset, limit, only=REQUEST_COMPANY.get()
        )
        totals = await interviews.counts(session, [item.id for item in rows])

    return [(item, totals.get(item.id, 0)) for item in rows]


async def with_credits(user_id: str, offset: int, limit: int) -> list[tuple[Company, dict]]:
    """The companies the user may top up, as an owner or admin, each with its credits."""
    async with Session() as session:
        rows = await companies.list_for_user(
            session, user_id, offset, limit, EDITORS, REQUEST_COMPANY.get()
        )

    credits = await billing.companies_credits([item.id for item in rows]) if rows else {}

    return [(item, credits[str(item.id)]) for item in rows]


async def referral(company_id) -> dict:
    """The company's referral code and rewards, each reward with its company's name."""
    found = await billing.company_referral(company_id)

    async with Session() as session:
        names = await companies.names(session, [row["company_id"] for row in found["rewards"]])

    return {**found, "names": names}
