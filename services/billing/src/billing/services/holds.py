"""Candidates' credits: set aside on invite, then charged once the interview finishes with an
answer, or given back."""

from fastapi import HTTPException, status
from prepza_common.events.analytics import track

from billing.constants.credits import CANDIDATE_CREDITS, CANDIDATE_PREFIX, NOT_ENOUGH, Reason
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.repositories import ledger
from billing.services.auto_top_up_charging import check_briefly


async def refuse(owner_type: str, owner_id: str, reason: str) -> None:
    await track("balance_too_low", company_id=owner_id, what=reason)
    # An automatic top-up refills it for the next try.
    await check_briefly(owner_type, owner_id)

    raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, NOT_ENOUGH)


async def hold(company_id: str, key: str) -> None:
    """Sets a candidate's credits aside (402 when too few are left); then charges an automatic
    top-up the balance now calls for, waited for only briefly."""
    async with Session.begin() as session:
        held = await ledger.reserve(
            session,
            OwnerType.COMPANY,
            company_id,
            CANDIDATE_CREDITS,
            CANDIDATE_PREFIX + key,
            Reason.CANDIDATE,
        )

    if not held:
        await refuse(OwnerType.COMPANY, company_id, Reason.CANDIDATE)

    await check_briefly(OwnerType.COMPANY, company_id)


async def charge(key: str) -> None:
    async with Session.begin() as session:
        await ledger.charge(session, CANDIDATE_PREFIX + key)


async def release(key: str) -> None:
    async with Session.begin() as session:
        await ledger.release(session, CANDIDATE_PREFIX + key)
