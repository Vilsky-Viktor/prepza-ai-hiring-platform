from datetime import datetime
from uuid import UUID

from prepza_common.config.constants import MAX_UPDATES

from app.constants.ats import ATS_NAMES
from app.constants.notifications import ATS_LINK
from app.integrations import companies
from app.schemas.ats import NotInvitedOut
from app.storage import not_invited


async def not_invited_between(
    company_ids: list[UUID], since: datetime, until: datetime
) -> list[NotInvitedOut]:
    """Each candidate of these companies' ATSs who first couldn't be invited between the two
    times and still isn't, the newest MAX_UPDATES, newest first, with their interview's title
    (from companies)."""
    rows = await not_invited.between(company_ids, since, until, MAX_UPDATES)
    interviews = await companies.interviews({row.interview_id for row, _ in rows})

    return [
        NotInvitedOut(
            at=row.failed_at,
            company_id=connection.company_id,
            interview_id=row.interview_id,
            title=interviews.get(row.interview_id, {}).get("title"),
            ats=ATS_NAMES[connection.provider],
            email=row.email,
            candidate_name=row.name,
            reason=row.reason,
            link=ATS_LINK.format(company_id=connection.company_id, provider=connection.provider),
        )
        for row, connection in rows
    ]
