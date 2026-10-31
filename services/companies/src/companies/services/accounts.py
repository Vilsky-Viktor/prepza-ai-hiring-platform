import asyncio

import httpx
from fastapi import HTTPException, status
from testee_common.config.constants import ACCOUNT_OWNS_SHARED

from companies.constants.roles import Role
from companies.core.db import Session
from companies.integrations import billing
from companies.repositories import accounts, audit, invites
from companies.services import candidate_billing, company_deletion


async def credits_of(company_id) -> int | None:
    """None when billing doesn't answer: the preview shows the company without them."""
    try:
        return (await billing.company_credits(company_id))["available"]
    except httpx.HTTPError:
        return None


async def deletion(user_id: str) -> dict:
    """What deleting the account does to the companies the user owns: one others have joined
    blocks it (another member is made owner first, or the company deleted); one only they are in
    is deleted with it, with its credits."""
    async with Session() as session:
        owned = await accounts.owned(session, user_id)

    alone = [company for company, shared in owned if not shared]
    credits = await asyncio.gather(*(credits_of(company.id) for company in alone))

    return {
        "blocked": [
            {"id": company.id, "name": company.name} for company, shared in owned if shared
        ],
        "deleted": [
            {"id": company.id, "name": company.name, "credits": left}
            for company, left in zip(alone, credits, strict=True)
        ],
    }


async def delete_user(user_id: str, email: str) -> None:
    """A company whose only owner leaves is deleted with them; other memberships just end.
    The user's candidate invites and their decisions in the audit log stay with the companies,
    without their email or id; team invites to their email not yet accepted go. Safe to repeat.
    Refused (409), before anything is deleted, while the user owns a company others have
    joined: it would go with their access and its credits. Accounts asks companies first, so no
    other service has deleted anything then. The memberships that end, the candidate invites,
    the team invites and the verification proof go in one save, so a failure keeps them all for
    the retry."""
    async with Session() as session:
        owned = await accounts.owned(session, user_id)
        memberships = await accounts.memberships(session, user_id)

    if any(shared for _, shared in owned):
        raise HTTPException(status.HTTP_409_CONFLICT, ACCOUNT_OWNS_SHARED)

    leaving = []

    for member, company, owner_count in memberships:
        if member.role == Role.OWNER and owner_count == 1:
            await company_deletion.delete_company(company.id)
        else:
            leaving.append(member.id)

    # As if the company removed them: one who picked an answer is charged, the others' credits
    # come back. Rounds still has their answers, as accounts asks companies first.
    async with Session() as session:
        unfinished = await accounts.unfinished_invites(session, user_id, email)

    await candidate_billing.settle_removed(unfinished)
    await forget(user_id, email, leaving)
    await audit.forget_user(Session, user_id)


async def forget(user_id: str, email: str, leaving: list) -> None:
    """In one save: the memberships that end, every invite the person was sent or started (as
    if each company erased them: a row kept without their email still linked back to them, so it
    wasn't anonymous; the other services are told, and a restore's copy is erased again), the
    team invites to their email and their email as a company's verification proof."""
    async with Session.begin() as session:
        for member_id in leaving:
            await accounts.remove_member(session, member_id)

        for invite, company_id in await accounts.candidate_invites(session, user_id, email):
            await invites.remove(session, invite, company_id)

        await accounts.forget_member_invites(session, email)
        await accounts.forget_verification_email(session, email)
