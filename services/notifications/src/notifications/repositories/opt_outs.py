from sqlalchemy import delete, exists, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from notifications.models.opt_outs import CandidateOptOut


async def add(
    session: AsyncSession,
    address: str,
    company_id: str,
    invite_id: str | None = None,
    by_admin: bool = False,
) -> None:
    """Stops the company's emails to the address (its hash), or with `invite_id` only that
    invite's reminders. Safe to repeat; a stop already there keeps who made it."""
    await session.execute(
        insert(CandidateOptOut)
        .values(address=address, company_id=company_id, invite_id=invite_id, by_admin=by_admin)
        .on_conflict_do_nothing()
    )


async def opted_out(
    session: AsyncSession, address: str, company_id: str, invite_id: str | None = None
) -> bool:
    """Whether the address (its hash) stopped the company's emails, or (given an invite) its
    reminders."""
    query = select(
        exists().where(
            CandidateOptOut.address == address,
            CandidateOptOut.company_id == company_id,
            or_(CandidateOptOut.invite_id.is_(None), CandidateOptOut.invite_id == invite_id),
        )
    )

    return bool(await session.scalar(query))


async def of_address(session: AsyncSession, address: str) -> list[CandidateOptOut]:
    """Every opt-out of the address (its hash): from a company's emails, or an invite's
    reminders."""
    query = select(CandidateOptOut).where(CandidateOptOut.address == address)

    return list(await session.scalars(query))


async def remove_admin_stop(session: AsyncSession, address: str, company_id: str) -> None:
    """Lifts the stop a superadmin made on the company's emails to the address (its hash). The
    candidate's own stops, from an email's link, stay: only they decided them. Safe to
    repeat."""
    await session.execute(
        delete(CandidateOptOut).where(
            CandidateOptOut.address == address,
            CandidateOptOut.company_id == company_id,
            CandidateOptOut.by_admin,
        )
    )


async def remove_company(session: AsyncSession, company_id: str) -> None:
    """A deleted company emails nobody again: its candidates' wishes go with it."""
    await session.execute(delete(CandidateOptOut).where(CandidateOptOut.company_id == company_id))
