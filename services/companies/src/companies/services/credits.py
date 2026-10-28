import asyncio
from uuid import UUID

from companies.core.db import Session
from companies.integrations import billing
from companies.repositories import credit_invites
from companies.schemas.companies import CompanyCreditsOut


async def holding(company_id: UUID) -> int:
    async with Session() as session:
        return await credit_invites.count_holding(session, company_id)


async def credits_of(company_id: UUID) -> CompanyCreditsOut:
    """The company's credits: available, set aside for candidates who haven't finished (and how
    many those are), whether they run low, and how many candidates they pay for."""
    credits, held = await asyncio.gather(billing.company_credits(company_id), holding(company_id))

    return CompanyCreditsOut(**credits, reserved_candidates=held)
