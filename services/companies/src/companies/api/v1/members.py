from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser, OptionalUser
from prepza_common.db.paging import PageParams

from companies.api.dependencies import Via
from companies.constants.roles import Role
from companies.core.db import Session
from companies.helpers.invite_links import addressed_to
from companies.models.companies import Member
from companies.repositories import members
from companies.schemas.companies import AdminInviteOut, MemberIn, MemberOut, MemberRoleIn
from companies.services import members as member_service
from companies.services.access import is_owner, require_company

router = APIRouter(prefix="/members", tags=["members"])


def member_out(member: Member, caller: Member) -> MemberOut:
    joined = member.user_id is not None

    return MemberOut(
        id=member.id,
        email=member.invited_email,
        role=member.role,
        joined=joined,
        token=None if joined else member.token,
        removable=is_owner(caller) and not is_owner(member),
        can_own=is_owner(caller) and joined and member.role == Role.ADMIN,
        created_at=member.created_at,
    )


@router.get("")
async def list_members(company_id: UUID, user: CurrentUser, page: PageParams) -> list[MemberOut]:
    company, caller = await require_company(user, company_id)

    async with Session() as session:
        rows = await members.list_for_company(session, company.id, page.offset, page.limit)

    return [member_out(member, caller) for member in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def invite_member(company_id: UUID, body: MemberIn, user: CurrentUser) -> MemberOut:
    """The owner invites an admin or a viewer, who is emailed the join link; the role applies
    once the invite is accepted."""
    company, caller = await require_company(user, company_id)

    if not is_owner(caller):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can add members")

    member = await member_service.invite(company, user, str(body.email).lower(), body.role)

    return member_out(member, caller)


async def owned_member(user: CurrentUser, company_id: UUID, member_id: UUID) -> Member:
    """A member or pending invite the owner manages; never the owner."""
    company, caller = await require_company(user, company_id)
    member = next((item for item in company.members if item.id == member_id), None)

    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

    if not is_owner(caller):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can manage members")

    if is_owner(member):
        raise HTTPException(status.HTTP_409_CONFLICT, "The owner can't be changed")

    return member


@router.put("/{member_id}/role", status_code=status.HTTP_204_NO_CONTENT)
async def change_role(
    company_id: UUID, member_id: UUID, body: MemberRoleIn, user: CurrentUser
) -> None:
    """The owner makes an admin a viewer or the other way round. A new viewer's automatic
    top-up goes off, as viewers spend no credits."""
    member = await owned_member(user, company_id, member_id)
    await member_service.change_role(company_id, member, body.role, user.uid)


@router.post("/{member_id}/owner", status_code=status.HTTP_204_NO_CONTENT)
async def make_owner(company_id: UUID, member_id: UUID, user: CurrentUser, via: Via) -> None:
    """The owner hands the company to a joined admin, who becomes its owner; the owner becomes an
    admin. Refused (409) for anyone else, and for someone who already owns as many companies as
    one person may."""
    member = await owned_member(user, company_id, member_id)
    company, caller = await require_company(user, company_id)
    await member_service.make_owner(company, caller, member, user.uid, via)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(company_id: UUID, member_id: UUID, user: CurrentUser) -> None:
    """The owner removes a member or withdraws a pending invite; never the owner. An automatic
    top-up paid with the removed member's card goes off, so it's never charged again."""
    member = await owned_member(user, company_id, member_id)
    await member_service.remove(company_id, member, user.uid)


@router.get("/invites/{token}")
async def get_admin_invite(token: str, user: OptionalUser) -> AdminInviteOut:
    """Open to visitors, so they see what they're invited to before signing in; whether it's the
    signed-in account's, and the invited email only to that account with it verified, so
    nobody else with the link learns it. A used link says so,
    and gives the company's id to the member who joined through it."""
    async with Session() as session:
        found = await members.get_by_token(session, token)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    member, company = found

    matches, email = addressed_to(user, member.invited_email)

    return AdminInviteOut(
        company_name=company.name,
        email=email,
        matches=matches,
        joined=member.user_id is not None,
        company_id=company.id if user and member.user_id == user.uid else None,
    )


@router.post("/invites/{token}/accept", status_code=status.HTTP_204_NO_CONTENT)
async def accept_admin_invite(token: str, user: CurrentUser) -> None:
    """Only the invited email can accept, so a forwarded link is useless to anyone else."""
    await member_service.accept(token, user)
