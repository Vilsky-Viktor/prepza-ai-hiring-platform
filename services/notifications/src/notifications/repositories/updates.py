from datetime import datetime

from prepza_common.events.notifications import Recipient
from sqlalchemy import select

from notifications.core.db import Session
from notifications.models.notifications import Notification


async def of_companies(
    company_ids: list[str], since: datetime, until: datetime
) -> list[Notification]:
    """The companies' notifications that came, or last grew (see add_to_group), after `since`
    and up to `until`, newest first. Each company keeps at most MAX_PER_RECIPIENT, so there are
    never many."""
    async with Session() as session:
        rows = await session.scalars(
            select(Notification)
            .where(
                Notification.recipient == Recipient.COMPANY,
                Notification.recipient_id.in_(company_ids),
                Notification.created_at > since,
                Notification.created_at <= until,
            )
            .order_by(Notification.created_at.desc())
        )

        return list(rows)
