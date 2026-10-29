"""Rows the integration tests make and remove, through the repositories in a transaction of
their own or the services that own the step, with the outcomes the tests compare."""

from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException
from prepza_common.auth.user import User
from sqlalchemy.exc import IntegrityError

from companies.repositories import companies, interviews, members
from companies.services import company_deletion, interview_removal
from companies.services import members as member_service
from companies.services.interview_access import interview_for
from tests.integration.transactions import transaction


async def company(name: str, user_id: str, email: str, most: int | None = None):
    """The company with its owner; None when another company has the name."""
    try:
        return await transaction(companies.create, name, user_id, email, most)
    except IntegrityError as error:
        if companies.name_taken(error):
            return None

        raise


async def renamed(company_id, name: str) -> bool:
    """False when another company has the name."""
    try:
        await transaction(companies.rename, company_id, name)
    except IntegrityError as error:
        if companies.name_taken(error):
            return False

        raise

    return True


async def member(company_id, email: str, role: str, sender: dict, most: int | None = None):
    """A pending team invite; None when the email was invited meanwhile."""
    try:
        return await transaction(members.add, company_id, email, role, sender, most)
    except IntegrityError:
        return None


async def accepted(invite, company, user_id: str) -> bool:
    """The invite accepted by `user_id` (as its invited email); False when it's gone."""
    user = User(uid=user_id, email=invite.invited_email, email_verified=True)

    try:
        await member_service.accept(invite.token, user)
    except HTTPException:
        return False

    return True


async def transferred(company, owner, admin, most: int | None = None) -> bool:
    """The company handed from `owner` to `admin`; False when either changed meanwhile."""
    return await member_service.transfer(company, owner, admin, owner.user_id, None, most)


async def deleted(company_id) -> None:
    """The company's rows go, as when it's deleted."""
    await company_deletion.delete_rows(company_id)


async def interview_removed(interview_id) -> list[tuple]:
    """The interview and its invites go; the unfinished ones' (interview id, email, status,
    hold key)."""
    return await interview_removal.remove(SimpleNamespace(id=interview_id))


async def team(kind: str = "team"):
    """A company with an interview and its owner, an admin and a viewer, each a fresh user id
    (`owner`, `admin`, `viewer`)."""
    users = {role: f"{kind}-{role}-{uuid4().hex[:12]}" for role in ("owner", "admin", "viewer")}
    owner = users["owner"]
    found = await company(f"{kind} {uuid4()}", owner, f"{owner}@example.com")

    for role in ("admin", "viewer"):
        invite = await member(found.id, f"{users[role]}@example.com", role, {})
        await accepted(invite, found, users[role])

    interview = await transaction(interviews.create, found.id, uuid4(), "en", 60)

    return SimpleNamespace(company=found, interview=interview, **users)


async def as_member(user_id: str, interview_id):
    """(interview, company, membership) as `user_id` reaches the interview."""
    user = User(uid=user_id, email=f"{user_id}@example.com", email_verified=True)

    return await interview_for(user, interview_id)
