# What the activity digest tells: companies' notifications of the digest's kinds in its window,
# and the notes written in it (pending_notes).
from datetime import datetime

from sqlalchemy import select, union
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events.notifications import Recipient

from notifications.models.notifications import Notification
from notifications.repositories import pending_notes


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
    session: AsyncSession,
    kinds: list[str],
    since: datetime,
    until: datetime,
    after: str,
    limit: int,
) -> list[str]:
    """A page of the companies that had such notifications or new notes: up to `limit` ids after
    `after`, in order."""
    notified = select(Notification.recipient_id.label("company_id")).where(
        *in_window(kinds, since, until), Notification.recipient_id > after
    )
    found = union(notified, pending_notes.company_ids(since, until, after)).subquery()
    rows = await session.scalars(
        select(found.c.company_id).order_by(found.c.company_id).limit(limit)
    )

    return list(rows)


async def companies_activity(
    session: AsyncSession,
    kinds: list[str],
    since: datetime,
    until: datetime,
    company_ids: list[str],
) -> list[Notification]:
    """Those companies' notifications of those kinds between those times."""
    rows = await session.scalars(
        select(Notification).where(
            *in_window(kinds, since, until), Notification.recipient_id.in_(company_ids)
        )
    )

    return list(rows)
