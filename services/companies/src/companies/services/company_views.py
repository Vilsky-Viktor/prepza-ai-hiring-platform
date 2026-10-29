"""The user's companies as the site lists them."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.roles import EDITORS, Role
from companies.core.db import Session
from companies.integrations import billing
from companies.models.companies import Company
from companies.repositories import companies, interviews
from companies.services.access import key_company


async def user_companies(
    session: AsyncSession,
    user_id: str,
    offset: int,
    limit: int,
    roles: tuple[str, ...] = tuple(Role),
) -> list[Company]:
    """The user's companies (only where their role is one of `roles`); for an AI agent signed in
    with an API key, the key's own, as an admin's."""
    keyed = key_company(user_id)

    if keyed is not None:
        found = await companies.get(session, UUID(keyed))

        return [found] if found is not None and offset == 0 else []

    return await companies.list_for_user(session, user_id, offset, limit, roles)


async def listed(user_id: str, offset: int, limit: int) -> list[tuple[Company, int]]:
    """The user's companies, each with its number of interviews; for an AI agent signed in with
    an API key, the key's only."""
    async with Session() as session:
        rows = await user_companies(session, user_id, offset, limit)
        totals = await interviews.counts(session, [item.id for item in rows])

    return [(item, totals.get(item.id, 0)) for item in rows]


async def with_credits(user_id: str, offset: int, limit: int) -> list[tuple[Company, dict]]:
    """The companies the user may top up, as an owner or admin, each with its credits."""
    async with Session() as session:
        rows = await user_companies(session, user_id, offset, limit, EDITORS)

    credits = await billing.companies_credits([item.id for item in rows]) if rows else {}

    return [(item, credits[str(item.id)]) for item in rows]


async def referral(company_id) -> dict:
    """The company's referral code and rewards, each reward with its company's name."""
    found = await billing.company_referral(company_id)

    async with Session() as session:
        names = await companies.names(session, [row["company_id"] for row in found["rewards"]])

    return {**found, "names": names}
