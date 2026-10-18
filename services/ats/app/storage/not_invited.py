from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.constants.ats import CandidateStatus
from app.models.ats import AtsCandidate, AtsConnection
from app.storage.db import Session


async def between(
    company_ids: list[UUID], since: datetime, until: datetime
) -> list[tuple[AtsCandidate, AtsConnection]]:
    """The companies' ATS candidates who first couldn't be invited after `since` and up to
    `until`, and still aren't, with their connections; newest first."""
    query = (
        select(AtsCandidate, AtsConnection)
        .join(AtsConnection, AtsConnection.id == AtsCandidate.connection_id)
        .where(
            AtsConnection.company_id.in_(company_ids),
            AtsCandidate.status == CandidateStatus.FAILED,
            AtsCandidate.failed_at > since,
            AtsCandidate.failed_at <= until,
        )
        .order_by(AtsCandidate.failed_at.desc())
    )

    async with Session() as session:
        return list(await session.execute(query))
