from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from library.models.legal import TermsAcceptance


async def accept_terms(session: AsyncSession, user_id: str, version: str) -> None:
    """Once per version: signing up again (a retried request) keeps the first time."""
    await session.execute(
        insert(TermsAcceptance).values(user_id=user_id, version=version).on_conflict_do_nothing()
    )


async def accepted_terms(session: AsyncSession, user_id: str) -> list[dict]:
    rows = await session.scalars(
        select(TermsAcceptance)
        .where(TermsAcceptance.user_id == user_id)
        .order_by(TermsAcceptance.accepted_at)
    )

    return [{"version": row.version, "at": row.accepted_at} for row in rows]
