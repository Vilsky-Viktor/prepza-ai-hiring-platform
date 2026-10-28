"""A company's team: the owner invites admins and viewers, changes their roles, removes them and
hands the company over; invitees join through their link. Each change is saved with its line in
the action log."""

import secrets

from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.limits.limits import at_most, limit
from prepza_common.limits.rate_limit import hit, hit_emails, recipient_key
from sqlalchemy.exc import IntegrityError

from companies.constants.roles import (
    ALREADY_INVITED,
    ONLY_ADMINS_OWN,
    OWNS_TOO_MANY,
    TOO_MANY_PENDING,
    Role,
)
from companies.core.db import Session
from companies.core.exceptions import OverLimit
from companies.helpers.logos import logo_path
from companies.helpers.notifications import member_joined, ownership_received
from companies.integrations import billing, billing_prices
from companies.integrations.redis import get_redis
from companies.models.companies import Company, Member
from companies.repositories import audit, companies, members, outbox
from companies.services import outbox as outbox_service


async def invite(company: Company, user: User, email: str, role: str) -> Member:
    """The owner invites an admin or a viewer (`email`, lowercased), who is emailed the join
    link; the role applies once the invite is accepted."""
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
    most = await limit(redis, "MAX_PENDING_INVITES")

    try:
        async with Session.begin() as session:
            member = await members.add(session, company.id, email, role, sender, most)
            await audit.record(
                session,
                company.id,
                user.uid,
                AuditAction.MEMBER_INVITED,
                member.id,
                target_kind=TargetKind.MEMBER,
            )
    except OverLimit as over:
        # Another invite took the last place meanwhile: counted again under its lock.
        await refuse_over(over.count)
        raise
    except IntegrityError:
        # Invited by another request at the same moment.
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_INVITED) from None

    # The email goes out now; the outbox's regular run sends it if this fails.
    await outbox_service.flush_quietly()

    return member


async def change_role(company_id, member: Member, role: str, user_id: str) -> None:
    """The owner makes an admin a viewer or the other way round. A new viewer's automatic
    top-up goes off first, as viewers spend no credits."""
    if role == Role.VIEWER and member.user_id is not None:
        await billing_prices.turn_off_auto_top_up(company_id, member.user_id)

    async with Session.begin() as session:
        await members.set_role(session, member.id, role)
        await audit.record(
            session,
            company_id,
            user_id,
            AuditAction.MEMBER_ROLE_CHANGED,
            member.id,
            target_kind=TargetKind.MEMBER,
        )


async def remove(company_id, member: Member, user_id: str) -> None:
    """The owner removes a member or withdraws a pending invite. An automatic top-up paid with
    the removed member's card goes off first, so it's never charged again."""
    if member.user_id is not None:
        await billing_prices.turn_off_auto_top_up(company_id, member.user_id)

    async with Session.begin() as session:
        await members.remove(session, member.id)
        await audit.record(
            session,
            company_id,
            user_id,
            AuditAction.MEMBER_REMOVED,
            member.id,
            target_kind=TargetKind.MEMBER,
        )


async def make_owner(
    company: Company, owner: Member, member: Member, user_id: str, via: str | None
) -> None:
    """The owner hands the company to a joined admin, who becomes its owner; the owner becomes an
    admin, in one save with the new owner's notification and the log's line. Refused (409) for
    anyone else, when either changed meanwhile (another transfer, a role change: a company never
    has two owners or none), and for someone who already owns as many companies as one person
    may, counted again under a lock."""
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

    async with Session() as session:
        await refuse_over(await companies.owned_count(session, member.user_id))

    most = await limit(get_redis(), "MAX_OWNED_COMPANIES")

    try:
        moved = await transfer(company, owner, member, user_id, via, most)
    except OverLimit as over:
        # They came to own another company meanwhile: counted again under its lock.
        await refuse_over(over.count)
        raise

    if not moved:
        raise HTTPException(status.HTTP_409_CONFLICT, ONLY_ADMINS_OWN)

    await outbox_service.flush_quietly()


async def transfer(
    company: Company,
    owner: Member,
    member: Member,
    user_id: str,
    via: str | None,
    most: int | None = None,
) -> bool:
    """False, with nothing changed, when the owner or the admin changed meanwhile."""
    async with Session.begin() as session:
        owned = await companies.lock_owner(session, member.user_id)

        if most is not None and owned >= most:
            raise OverLimit(owned)

        both = await members.lock_both(session, owner.id, member.id)
        ready = both is not None and both[0].role == Role.OWNER and both[1].role == Role.ADMIN

        if not ready or both[1].user_id is None:
            return False

        await members.set_role(session, owner.id, Role.ADMIN)
        await members.set_role(session, member.id, Role.OWNER)
        outbox.notify(session, ownership_received(company, member, secrets.token_hex(8)))
        await audit.record(
            session,
            company.id,
            user_id,
            AuditAction.OWNERSHIP_TRANSFERRED,
            member.id,
            via=via,
            target_kind=TargetKind.MEMBER,
        )

    return True


async def accept(token: str, user: User) -> None:
    """Only the invited email can accept, so a forwarded link is useless to anyone else. Joins
    the member, with the log's line and the owner's notification, in one save; locked, so two
    clicks at once join and tell once. 404 when there's no such invite, or it was removed
    meanwhile."""
    async with Session.begin() as session:
        found = await members.get_by_token(session, token)

        if found is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

        member, company = found

        if not user.email_verified or user.email.lower() != member.invited_email:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "This invite was sent to a different email address"
            )

        row, joining = await members.join(session, member.id, user.uid)

        if joining:
            await audit.record(
                session,
                company.id,
                user.uid,
                AuditAction.MEMBER_JOINED,
                row.id,
                target_kind=TargetKind.MEMBER,
            )
            owner_id = await members.owner_user_id(session, company.id)

            if owner_id:
                outbox.notify(session, member_joined(company, row, owner_id))

    # Removed meanwhile by the owner.
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    # The owner's notification goes out now; the outbox's regular run sends it if this fails.
    await outbox_service.flush_quietly()
