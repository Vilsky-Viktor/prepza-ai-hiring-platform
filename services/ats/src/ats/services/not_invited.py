from datetime import datetime
from uuid import UUID

from prepza_common.config.constants import MAX_UPDATES

from ats.constants.ats import ATS_NAMES
from ats.constants.notifications import ATS_LINK
from ats.core.db import Session
from ats.integrations import companies
from ats.repositories import not_invited
from ats.schemas.ats import NotInvitedListOut, NotInvitedOut


async def not_invited_between(
    company_ids: list[UUID], since: datetime, until: datetime
) -> NotInvitedListOut:
    """Each candidate of these companies' ATSs who first couldn't be invited between the two
    times and still isn't, the newest MAX_UPDATES, newest first, with their interview's title
    (from companies), and how many there are in all."""
    async with Session() as session:
        rows = await not_invited.between(session, company_ids, since, until, MAX_UPDATES)
        total = await not_invited.count_between(session, company_ids, since, until)

    interviews = await companies.interviews({row.interview_id for row, _ in rows})
    items = [
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

    return NotInvitedListOut(items=items, total=total)
