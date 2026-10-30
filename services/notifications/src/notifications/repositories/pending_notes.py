# The digest's copy of the notes written in the last PENDING_NOTE_HOURS (models/pending_notes.py).
from datetime import datetime

from prepza_common.db.db import delete_in_batches
from sqlalchemy import String, cast, delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from notifications.models.pending_notes import PendingNote


async def save(session: AsyncSession, note: dict, excerpt: str, since: datetime) -> None:
    """Keeps a note written after `since` (an older one is past every digest), or its newer
    text: a later edit wins over an earlier one and over the note as first written, whatever
    order their events come in."""
    if note["created_at"] < since:
        return

    values = {
        "company_id": note["company_id"],
        "interview_id": note["interview_id"],
        "title": note["title"],
        "author_id": note["author_id"],
        "author_name": note["author_name"],
        "excerpt": excerpt,
        "created_at": note["created_at"],
        "edited_at": note["edited_at"],
    }
    query = insert(PendingNote).values(note_id=note["note_id"], **values)
    newer = query.excluded.edited_at.is_not(None) & or_(
        PendingNote.edited_at.is_(None), PendingNote.edited_at < query.excluded.edited_at
    )
    await session.execute(
        query.on_conflict_do_update(
            index_elements=["note_id"],
            set_={"excerpt": excerpt, "edited_at": query.excluded.edited_at},
            where=newer,
        )
    )


async def remove(session: AsyncSession, note_id: str) -> None:
    await session.execute(delete(PendingNote).where(PendingNote.note_id == note_id))


async def remove_interview(session: AsyncSession, interview_id: str) -> None:
    await session.execute(delete(PendingNote).where(PendingNote.interview_id == interview_id))


async def remove_company(session: AsyncSession, company_id: str) -> None:
    await session.execute(delete(PendingNote).where(PendingNote.company_id == company_id))


async def forget_author(session: AsyncSession, user_id: str) -> None:
    """A deleted account's notes stay the company's, as a former member's."""
    await session.execute(
        update(PendingNote)
        .where(PendingNote.author_id == user_id)
        .values(author_id=None, author_name=None)
    )


def in_window(since: datetime, until: datetime) -> tuple:
    return PendingNote.created_at >= since, PendingNote.created_at < until


def company_ids(since: datetime, until: datetime, after: str):
    """The companies with notes written between those times, after `after`, as text (to page
    them with the bell's companies)."""
    company_id = cast(PendingNote.company_id, String)

    return select(company_id.label("company_id")).where(
        *in_window(since, until), company_id > after
    )


async def of_companies(
    session: AsyncSession, company_ids: list[str], since: datetime, until: datetime
) -> list[PendingNote]:
    """Those companies' notes written between those times, newest first."""
    rows = await session.scalars(
        select(PendingNote)
        .where(PendingNote.company_id.in_(company_ids), *in_window(since, until))
        .order_by(PendingNote.created_at.desc())
    )

    return list(rows)


async def forget(sessions, before: datetime, until: float | None = None) -> None:
    """Notes written before `before` go, in batches (each its own transaction), none started
    after `until` (time.monotonic()); the next run deletes the rest."""
    await delete_in_batches(sessions, PendingNote, PendingNote.created_at < before, until=until)
