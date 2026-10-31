# The bell's items about the team's notes: one per member and interview while it's unread, its
# data holding the interview, how many notes it groups, its latest notes (helpers/notes.py) and
# their latest authors.
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.events.notifications import NotificationKind, Recipient

from notifications.helpers.notes import authors_of
from notifications.models.notifications import Notification, Seen


def note_items():
    return Notification.kind == NotificationKind.NOTE_ADDED


async def lock_note(session: AsyncSession, note_id: str) -> None:
    """A note's events are handled one at a time, so a deletion never misses the items its
    note is being added to."""
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(f"note:{note_id}"))))


async def unread_group(session: AsyncSession, user_id: str, link: str) -> Notification | None:
    """The user's item about the notes behind `link` that came after they last opened the bell,
    locked to add to it."""
    seen_at = await session.scalar(select(Seen.seen_at).where(Seen.user_id == user_id))
    query = select(Notification).where(
        Notification.recipient == Recipient.USER,
        Notification.recipient_id == user_id,
        note_items(),
        Notification.link == link,
    )

    if seen_at is not None:
        query = query.where(Notification.created_at > seen_at)

    return await session.scalar(
        query.order_by(Notification.created_at.desc()).limit(1).with_for_update()
    )


async def holding(session: AsyncSession, interview_id: str, filters: dict) -> list[Notification]:
    """The interview's note items whose data contains `filters` (a note, an author), locked."""
    rows = await session.scalars(
        select(Notification)
        .where(
            note_items(),
            Notification.data["interview_id"].astext == interview_id,
            Notification.data.contains(filters),
        )
        .with_for_update()
    )

    return list(rows)


async def by_author(session: AsyncSession, author_id: str) -> list[Notification]:
    """Every note item naming a note by `author_id`, locked."""
    rows = await session.scalars(
        select(Notification)
        .where(note_items(), Notification.data.contains({"notes": [{"author_id": author_id}]}))
        .with_for_update()
    )

    return list(rows)


async def set_notes(session: AsyncSession, item: Notification, notes: list, count: int) -> None:
    """The item with these notes and count, or gone with its last note."""
    if count <= 0:
        await session.delete(item)

        return

    item.data = {**item.data, "count": count, "notes": notes, "authors": authors_of(notes)}


async def remove_interview(session: AsyncSession, interview_id: str) -> None:
    await session.execute(
        delete(Notification).where(
            note_items(), Notification.data["interview_id"].astext == interview_id
        )
    )


async def remove_company(session: AsyncSession, company_id: str) -> None:
    """A deleted company's note items, in every member's bell."""
    await session.execute(
        delete(Notification).where(
            note_items(), Notification.data["company_id"].astext == company_id
        )
    )


async def add(session: AsyncSession, user_id: str, link: str, data: dict, now: datetime) -> None:
    """A new item for the user, keyed by its first note and the user."""
    session.add(
        Notification(
            event_id=f"note:{data['notes'][0]['id']}:{user_id}",
            recipient=Recipient.USER,
            recipient_id=user_id,
            kind=NotificationKind.NOTE_ADDED,
            link=link,
            data=data,
            created_at=now,
        )
    )
    await session.flush()
