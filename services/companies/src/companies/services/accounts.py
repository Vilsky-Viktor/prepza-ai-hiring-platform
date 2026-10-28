import asyncio

import httpx
from fastapi import HTTPException, status
from prepza_common.config.constants import ACCOUNT_OWNS_SHARED

from companies.constants.roles import Role
from companies.integrations import billing
from companies.repositories import accounts, audit
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
    owned = await accounts.owned(user_id)
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
    without their email or id; team invites to their email not yet accepted go. Safe to repeat. Refused (409), before anything is deleted, while
    the user owns a company others have joined: it would go with their access and its credits.
    Library asks companies first, so no other service has deleted anything then."""
    if any(shared for _, shared in await accounts.owned(user_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, ACCOUNT_OWNS_SHARED)

    for member, company, owner_count in await accounts.memberships(user_id):
        if member.role == Role.OWNER and owner_count == 1:
            await company_deletion.delete_company(company.id)
        else:
            await accounts.remove_member(member.id)

    # As if the company removed them: one who picked an answer is charged, the others' credits
    # come back. Rounds still has their answers, as library asks companies first.
    await candidate_billing.settle_removed(await accounts.unfinished_invites(user_id, email))
    await accounts.forget_candidate(user_id, email)
    await accounts.forget_member_invites(email)
    await accounts.forget_verification_email(email)
    await audit.forget_user(user_id)
