import secrets

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import MEMBER_INVITED
from companies.constants.roles import Role
from companies.core.exceptions import OverLimit
from companies.models.companies import Company, Member
from companies.repositories import outbox


async def add(
    session: AsyncSession,
    company_id,
    email: str,
    role: str,
    sender: dict,
    most: int | None = None,
) -> Member:
    """A pending invite; the role applies once it's accepted. Its email's event is saved with it:
    `sender` (the company, its logo, the inviter and their language) and the join link's token.
    An IntegrityError when the email was invited meanwhile; OverLimit when the company already
    has `most` pending invites, counted under a lock (two invites at once can't both pass)."""
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

    lock = func.pg_advisory_xact_lock(func.hashtext(f"pending-invites:{company_id}"))
    await session.execute(select(lock))
    count = await session.scalar(pending)

    if most is not None and count >= most:
        raise OverLimit(count)

    session.add(member)
    outbox.add(
        session,
        MEMBER_INVITED,
        {**sender, "email": member.invited_email, "token": member.token, "role": role},
    )
    await session.flush()

    return member


async def get_by_token(session: AsyncSession, token: str) -> tuple[Member, Company] | None:
    query = (
        select(Member, Company)
        .join(Company, Company.id == Member.company_id)
        .where(Member.token == token)
    )

    row = (await session.execute(query)).first()

    return tuple(row) if row else None


async def join(session: AsyncSession, member_id, user_id: str) -> tuple[Member | None, bool]:
    """The invite, locked, so two clicks at once join once, and whether it joined `user_id` now;
    (None, False) when it was removed meanwhile. The link stays, so reopening it says it was used
    (and opens the company for its member) instead of "invalid"; joining twice changes nothing."""
    # Fresh from the database once locked, though the session may hold it already.
    query = (
        select(Member)
        .where(Member.id == member_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    row = await session.scalar(query)

    if row is None or row.user_id is not None:
        return row, False

    row.user_id = user_id

    return row, True


async def owner_user_id(session: AsyncSession, company_id) -> str | None:
    return await session.scalar(
        select(Member.user_id).where(Member.company_id == company_id, Member.role == Role.OWNER)
    )


async def lock_both(session: AsyncSession, owner_id, member_id) -> tuple[Member, Member] | None:
    """The owner's and the member's rows, locked in one order so two transfers at once can't
    wait on each other; None when either is gone."""
    rows = await session.scalars(
        select(Member)
        .where(Member.id.in_([owner_id, member_id]))
        .order_by(Member.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    found = {row.id: row for row in rows}

    if owner_id not in found or member_id not in found:
        return None

    return found[owner_id], found[member_id]


async def list_for_company(
    session: AsyncSession, company_id, offset: int, limit: int
) -> list[Member]:
    query = (
        select(Member)
        .where(Member.company_id == company_id)
        .order_by(Member.created_at, Member.id)
        .offset(offset)
        .limit(limit)
    )

    return list(await session.scalars(query))


async def set_role(session: AsyncSession, member_id, role: str) -> None:
    await session.execute(update(Member).where(Member.id == member_id).values(role=role))


async def remove(session: AsyncSession, member_id) -> None:
    await session.execute(delete(Member).where(Member.id == member_id))
