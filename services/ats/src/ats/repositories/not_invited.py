from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ats.constants.ats import CandidateStatus
from ats.models.ats import AtsCandidate, AtsConnection


def failed_between(company_ids: list[UUID], since: datetime, until: datetime) -> list:
    """The companies' ATS candidates who first couldn't be invited after `since` and up to
    `until`, and still aren't."""
    return [
        AtsConnection.company_id.in_(company_ids),
        AtsCandidate.status == CandidateStatus.FAILED,
        AtsCandidate.failed_at > since,
        AtsCandidate.failed_at <= until,
    ]


async def between(
    session: AsyncSession, company_ids: list[UUID], since: datetime, until: datetime, limit: int
) -> list[tuple[AtsCandidate, AtsConnection]]:
    """Up to `limit` of them (failed_between), newest first, with their connections."""
    query = (
        select(AtsCandidate, AtsConnection)
        .join(AtsConnection, AtsConnection.id == AtsCandidate.connection_id)
        .where(*failed_between(company_ids, since, until))
        .order_by(AtsCandidate.failed_at.desc())
        .limit(limit)
    )

    return list(await session.execute(query))


async def count_between(
    session: AsyncSession, company_ids: list[UUID], since: datetime, until: datetime
) -> int:
    """How many there are in all (failed_between)."""
    query = (
        select(func.count())
        .select_from(AtsCandidate)
        .join(AtsConnection, AtsConnection.id == AtsCandidate.connection_id)
        .where(*failed_between(company_ids, since, until))
    )

    return await session.scalar(query)
