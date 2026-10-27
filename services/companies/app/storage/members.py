import secrets

from prepza_common.events import outbox
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError

from app.constants.events import MEMBER_INVITED
from app.constants.roles import Role
from app.core.exceptions import OverLimit
from app.helpers.notifications import member_joined, ownership_received
from app.models.companies import Company, Member
from app.models.outbox import OutboxEvent
from app.storage import audit
from app.storage.companies import lock_owner
from app.storage.db import Session


async def add(
    company_id,
    email: str,
    role: str,
    sender: dict,
    most: int | None = None,
) -> Member | None:
    """A pending invite; the role applies once it's accepted. Its email's event is saved with it:
    `sender` (the company, its logo, the inviter and their language) and the join link's token.
    None when the email was invited meanwhile; OverLimit when the company already has `most`
    pending invites, counted under a lock (two invites at once can't both pass)."""
    member = Member(
        company_id=company_id,
        invited_email=email.lower(),
        role=role,
        token=secrets.token_urlsafe(32),
    )

    pending = (
        select(func.count())
        .select_from(Member)
        .where(Member.company_id == company_id, Member.user_id.is_(None))
    )

    async with Session() as session:
        lock = func.pg_advisory_xact_lock(func.hashtext(f"pending-invites:{company_id}"))
        await session.execute(select(lock))
        count = await session.scalar(pending)

        if most is not None and count >= most:
            raise OverLimit(count)

        session.add(member)
        outbox.add(
            session,
            OutboxEvent,
            MEMBER_INVITED,
            {**sender, "email": member.invited_email, "token": member.token, "role": role},
        )

        try:
            await session.commit()
        except IntegrityError:
            return None

    return member


async def get_by_token(token: str) -> tuple[Member, Company] | None:
    query = (
        select(Member, Company)
        .join(Company, Company.id == Member.company_id)
        .where(Member.token == token)
    )

    async with Session() as session:
        row = (await session.execute(query)).first()

        return tuple(row) if row else None


async def accept(member: Member, company: Company, user_id: str) -> bool:
    """Joins the member, and tells the owner in the bell, in the same transaction; locked, so
    two clicks at once join and tell once. False when the invite was removed meanwhile."""
    async with Session() as session:
        row = await session.scalar(select(Member).where(Member.id == member.id).with_for_update())

        if row is None:
            return False

        joining = row.user_id is None

        if joining:
            row.user_id = user_id
            session.add(
                audit.row(
                    company.id,
                    user_id,
                    AuditAction.MEMBER_JOINED,
                    row.id,
                    target_kind=TargetKind.MEMBER,
                )
            )

        # The link stays, so reopening it says it was used (and opens the company for its
        # member) instead of "invalid"; joining twice changes nothing.

        owner_id = await session.scalar(
            select(Member.user_id).where(Member.company_id == company.id, Member.role == Role.OWNER)
        )

        if joining and owner_id:
            outbox.add(
                session, OutboxEvent, NOTIFICATION_REQUESTED, member_joined(company, row, owner_id)
            )

        await session.commit()

    return True


async def transfer_ownership(
    company: Company,
    owner: Member,
    member: Member,
    most: int | None = None,
) -> bool:
    """Makes `member`, a joined admin, the owner, and the owner an admin, in one transaction with
    the new owner's notification. False when either changed meanwhile (another transfer, a role
    change): nothing changes then, so a company never has two owners or none. OverLimit when
    `member` already owns `most` companies, counted under a lock."""
    async with Session() as session:
        owned = await lock_owner(session, member.user_id)

        if most is not None and owned >= most:
            raise OverLimit(owned)

        stepped_down = await session.execute(
            update(Member)
            .where(Member.id == owner.id, Member.role == Role.OWNER)
            .values(role=Role.ADMIN)
        )
        stepped_up = await session.execute(
            update(Member)
            .where(Member.id == member.id, Member.role == Role.ADMIN, Member.user_id.is_not(None))
            .values(role=Role.OWNER)
        )

        if stepped_down.rowcount != 1 or stepped_up.rowcount != 1:
            await session.rollback()

            return False

        notice = ownership_received(company, member, secrets.token_hex(8))
        outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)
        await session.commit()

        return True


async def list_for_company(company_id, offset: int, limit: int) -> list[Member]:
    query = (
        select(Member)
        .where(Member.company_id == company_id)
        .order_by(Member.created_at, Member.id)
        .offset(offset)
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def set_role(member_id, role: str) -> None:
    async with Session() as session:
        await session.execute(update(Member).where(Member.id == member_id).values(role=role))
        await session.commit()


async def remove(member_id) -> None:
    async with Session() as session:
        await session.execute(delete(Member).where(Member.id == member_id))
        await session.commit()
