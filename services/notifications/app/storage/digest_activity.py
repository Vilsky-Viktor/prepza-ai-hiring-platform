# What the activity digest tells: companies' notifications of the digest's kinds in its window.
from datetime import datetime

from prepza_common.events.notifications import Recipient
from sqlalchemy import select

from app.models.notifications import Notification
from app.storage.db import Session


def in_window(kinds: list[str], since: datetime, until: datetime) -> tuple:
    """Companies' notifications of those kinds that came, or last grew (see
    notifications.add_to_group), between those times."""
    return (
        Notification.recipient == Recipient.COMPANY,
        Notification.kind.in_(kinds),
        Notification.created_at >= since,
        Notification.created_at < until,
    )


async def active_companies(
    kinds: list[str], since: datetime, until: datetime, after: str, limit: int
) -> list[str]:
    """A page of the companies that had such notifications: up to `limit` ids after `after`, in
    order."""
    async with Session() as session:
        rows = await session.scalars(
            select(Notification.recipient_id)
            .where(*in_window(kinds, since, until), Notification.recipient_id > after)
            .distinct()
            .order_by(Notification.recipient_id)
            .limit(limit)
        )

        return list(rows)


async def companies_activity(
    kinds: list[str], since: datetime, until: datetime, company_ids: list[str]
) -> list[Notification]:
    """Those companies' notifications of those kinds between those times."""
    async with Session() as session:
        rows = await session.scalars(
            select(Notification).where(
                *in_window(kinds, since, until), Notification.recipient_id.in_(company_ids)
            )
        )

        return list(rows)
