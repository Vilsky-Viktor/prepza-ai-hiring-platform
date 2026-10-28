from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from companies.helpers.search import escape_like
from companies.models.companies import Company, Member


async def search(session: AsyncSession, q: str, limit: int) -> list[tuple[Company, int]]:
    """Companies whose name has `q` in it, whatever its case (all when empty), newest first, each
    with how many people joined it."""
    joined = (
        select(func.count())
        .where(Member.company_id == Company.id, Member.user_id.is_not(None))
        .correlate(Company)
        .scalar_subquery()
    )
    query = select(Company, joined).order_by(Company.created_at.desc()).limit(limit)

    if q:
        query = query.where(Company.name.ilike(f"%{escape_like(q.lower())}%", escape="\\"))

    return [tuple(row) for row in await session.execute(query)]


async def set_suspended(session: AsyncSession, company_id, suspended: bool) -> bool:
    """False when there's no such company."""
    query = (
        update(Company)
        .where(Company.id == company_id)
        .values(suspended_at=datetime.now(UTC) if suspended else None)
        .returning(Company.id)
    )

    found = await session.scalar(query)

    return found is not None
