from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser, OptionalUser
from prepza_common.db.paging import PageParams
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.limits.limits import at_most, limit
from prepza_common.limits.rate_limit import hit, hit_emails, recipient_key

from app.constants.roles import (
    ALREADY_INVITED,
    ONLY_ADMINS_OWN,
    OWNS_TOO_MANY,
    TOO_MANY_PENDING,
    Role,
)
from app.core.exceptions import OverLimit
from app.helpers.invite_links import addressed_to
from app.helpers.logos import logo_path
from app.integrations import billing, billing_prices
from app.integrations.redis import get_redis
from app.models.companies import Member
from app.schemas.companies import AdminInviteOut, MemberIn, MemberOut, MemberRoleIn
from app.service_auth import Via
from app.services import outbox as outbox_service
from app.services.access import is_owner, require_company
from app.storage import audit, companies, members

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
    rows = await members.list_for_company(company.id, page.offset, page.limit)

    return [member_out(member, caller) for member in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def invite_member(company_id: UUID, body: MemberIn, user: CurrentUser) -> MemberOut:
    """The owner invites an admin or a viewer, who is emailed the join link; the role applies
    once the invite is accepted."""
    company, caller = await require_company(user, company_id)

    if not is_owner(caller):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can add members")

    email = str(body.email).lower()

    if email == user.email.lower():
        raise HTTPException(status.HTTP_409_CONFLICT, "You're already a member")

    if any(member.invited_email == email for member in company.members):
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_INVITED)

    redis = get_redis()
    who = {"company_id": company.id, "user_id": user.uid}

    async def refuse_over(count: int) -> None:
        await at_most(
            redis, "MAX_PENDING_INVITES", count, status.HTTP_409_CONFLICT, TOO_MANY_PENDING, **who
        )

    await refuse_over(sum(member.user_id is None for member in company.members))

    # The invite emails the member, so it counts toward the owner's email limits: the narrower
    # ones (the owner, this address) first, so one refused address doesn't use up the company's.
    await hit_emails(redis, user.uid, f"member:{company.id}:{recipient_key(email)}", company.id)

    if not await billing.company_paid(company.id):
        key = f"rate:member-invites:{company.id}"
        await hit(redis, key, "MEMBER_INVITES_PER_UNPAID_DAY", **who)
    sender = {
        "company": company.name,
        "company_id": str(company.id),
        "logo_path": logo_path(company),
        "inviter": user.name or user.email,
        "language": user.language,
    }

    try:
        most = await limit(redis, "MAX_PENDING_INVITES")
        member = await members.add(company.id, email, body.role, sender, most)
    except OverLimit as over:
        # Another invite took the last place meanwhile: counted again under its lock.
        await refuse_over(over.count)
        raise

    # Invited by another request at the same moment.
    if member is None:
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_INVITED)
    await audit.record(
        company.id, user.uid, AuditAction.MEMBER_INVITED, member.id, target_kind=TargetKind.MEMBER
    )
    # The email goes out now; the outbox's regular run sends it if this fails.
    await outbox_service.flush_quietly()

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

    if body.role == Role.VIEWER and member.user_id is not None:
        await billing_prices.turn_off_auto_top_up(company_id, member.user_id)

    await members.set_role(member.id, body.role)
    await audit.record(
        company_id,
        user.uid,
        AuditAction.MEMBER_ROLE_CHANGED,
        member.id,
        target_kind=TargetKind.MEMBER,
    )


@router.post("/{member_id}/owner", status_code=status.HTTP_204_NO_CONTENT)
async def make_owner(company_id: UUID, member_id: UUID, user: CurrentUser, via: Via) -> None:
    """The owner hands the company to a joined admin, who becomes its owner; the owner becomes an
    admin. Refused (409) for anyone else, and for someone who already owns as many companies as
    one person may."""
    member = await owned_member(user, company_id, member_id)
    company, caller = await require_company(user, company_id)

    if member.user_id is None or member.role != Role.ADMIN:
        raise HTTPException(status.HTTP_409_CONFLICT, ONLY_ADMINS_OWN)

    async def refuse_over(count: int) -> None:
        await at_most(
            get_redis(),
            "MAX_OWNED_COMPANIES",
            count,
            status.HTTP_409_CONFLICT,
            OWNS_TOO_MANY,
            company_id=company.id,
            user_id=member.user_id,
        )

    await refuse_over(await companies.owned_count(member.user_id))

    most = await limit(get_redis(), "MAX_OWNED_COMPANIES")

    try:
        moved = await members.transfer_ownership(company, caller, member, most)
    except OverLimit as over:
        # They came to own another company meanwhile: counted again under its lock.
        await refuse_over(over.count)
        raise

    if not moved:
        raise HTTPException(status.HTTP_409_CONFLICT, ONLY_ADMINS_OWN)

    await audit.record(
        company.id,
        user.uid,
        AuditAction.OWNERSHIP_TRANSFERRED,
        member.id,
        via=via,
        target_kind=TargetKind.MEMBER,
    )
    await outbox_service.flush_quietly()


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(company_id: UUID, member_id: UUID, user: CurrentUser) -> None:
    """The owner removes a member or withdraws a pending invite; never the owner. An automatic
    top-up paid with the removed member's card goes off, so it's never charged again."""
    member = await owned_member(user, company_id, member_id)

    if member.user_id is not None:
        await billing_prices.turn_off_auto_top_up(company_id, member.user_id)

    await members.remove(member.id)
    await audit.record(
        company_id, user.uid, AuditAction.MEMBER_REMOVED, member.id, target_kind=TargetKind.MEMBER
    )


@router.get("/invites/{token}")
async def get_admin_invite(token: str, user: OptionalUser) -> AdminInviteOut:
    """Open to visitors, so they see what they're invited to before signing in; whether it's the
    signed-in account's, and the invited email only to that account with it verified, so
    nobody else with the link learns it. A used link says so,
    and gives the company's id to the member who joined through it."""
    found = await members.get_by_token(token)

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
    found = await members.get_by_token(token)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    member, company = found

    if not user.email_verified or user.email.lower() != member.invited_email:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "This invite was sent to a different email address"
        )

    # Removed meanwhile by the owner.
    if not await members.accept(member, company, user.uid):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    # The owner's notification goes out now; the outbox's regular run sends it if this fails.
    await outbox_service.flush_quietly()
