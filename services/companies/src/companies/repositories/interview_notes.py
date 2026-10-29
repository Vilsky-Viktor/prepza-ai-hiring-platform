from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from companies.models.companies import Company, Member
from companies.models.interview_notes import InterviewNote
from companies.models.interviews import Interview


async def page(
    session: AsyncSession, company_id, interview_id, offset: int, limit: int
) -> list[tuple[InterviewNote, Member | None]]:
    """The interview's notes, the pinned one first, then newest first, each with its author's
    membership (None for a former member)."""
    query = (
        select(InterviewNote, Member)
        .outerjoin(Member, Member.id == InterviewNote.author_member_id)
        .where(InterviewNote.company_id == company_id, InterviewNote.interview_id == interview_id)
        .order_by(InterviewNote.pinned.desc(), InterviewNote.created_at.desc(), InterviewNote.id)
        .offset(offset)
        .limit(limit)
    )

    return [tuple(row) for row in await session.execute(query)]


async def summaries(session: AsyncSession, interview_ids: list) -> dict:
    """Each interview's number of notes and its pinned note's text, in one query: {interview id:
    (count, pinned text or None)}; interviews without notes are left out."""
    if not interview_ids:
        return {}

    pinned = func.max(InterviewNote.text).filter(InterviewNote.pinned)
    query = (
        select(InterviewNote.interview_id, func.count(), pinned)
        .where(InterviewNote.interview_id.in_(interview_ids))
        .group_by(InterviewNote.interview_id)
    )

    return {row[0]: (row[1], row[2]) for row in await session.execute(query)}


async def get(session: AsyncSession, interview_id, note_id) -> InterviewNote | None:
    query = select(InterviewNote).where(
        InterviewNote.id == note_id, InterviewNote.interview_id == interview_id
    )

    return await session.scalar(query)


async def add(session: AsyncSession, interview: Interview, member_id, text: str) -> InterviewNote:
    note = InterviewNote(
        company_id=interview.company_id,
        interview_id=interview.id,
        author_member_id=member_id,
        text=text,
    )
    session.add(note)
    await session.flush()

    return note


async def set_text(session: AsyncSession, note: InterviewNote, text: str) -> None:
    note.text = text
    note.edited_at = datetime.now(UTC)
    await session.flush()


async def remove(session: AsyncSession, note_id) -> None:
    await session.execute(delete(InterviewNote).where(InterviewNote.id == note_id))


async def set_pinned(session: AsyncSession, interview_id, note_id, pinned: bool) -> None:
    """Pins the note, unpinning the interview's other one first (the unique index allows one),
    or unpins it. The interview's row is locked first, so two pins at once take turns."""
    await session.scalar(select(Interview.id).where(Interview.id == interview_id).with_for_update())

    if pinned:
        await session.execute(
            update(InterviewNote)
            .where(InterviewNote.interview_id == interview_id, InterviewNote.pinned)
            .values(pinned=False)
        )

    await session.execute(
        update(InterviewNote).where(InterviewNote.id == note_id).values(pinned=pinned)
    )


async def authored(session: AsyncSession, user_id: str) -> list[tuple]:
    """Every note the user wrote as a member, for their data export: (company, interview, text,
    written, edited), oldest first."""
    query = (
        select(
            Company.name,
            Interview.title,
            InterviewNote.text,
            InterviewNote.created_at,
            InterviewNote.edited_at,
        )
        .join(Member, Member.id == InterviewNote.author_member_id)
        .join(Company, Company.id == InterviewNote.company_id)
        .join(Interview, Interview.id == InterviewNote.interview_id)
        .where(Member.user_id == user_id)
        .order_by(InterviewNote.created_at)
    )

    return [tuple(row) for row in await session.execute(query)]
