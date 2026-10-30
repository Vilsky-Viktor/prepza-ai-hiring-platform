# An interview's notes as events for notifications (the bell, Slack and the digest), saved in the
# outbox with the change they tell of.
from prepza_common.events.notes import (
    NOTE_CREATED,
    NOTE_DELETED,
    NOTE_EDITED,
    NoteDeleted,
    NoteWritten,
)
from sqlalchemy.ext.asyncio import AsyncSession

from companies.models.interview_notes import InterviewNote
from companies.models.interviews import Interview
from companies.repositories import outbox


def written(
    session: AsyncSession,
    interview: Interview,
    note: InterviewNote,
    author_id: str,
    author_name: str | None,
) -> None:
    """A note just written, or edited (it has `edited_at`), with its author as the team sees
    them."""
    data = NoteWritten(
        note_id=note.id,
        company_id=interview.company_id,
        interview_id=interview.id,
        title=interview.title,
        author_id=author_id,
        author_name=author_name,
        text=note.text,
        created_at=note.created_at,
        edited_at=note.edited_at,
    ).model_dump(mode="json")
    outbox.add(session, NOTE_EDITED if note.edited_at else NOTE_CREATED, data)


def deleted(session: AsyncSession, interview: Interview, note_id) -> None:
    data = NoteDeleted(
        note_id=note_id, company_id=interview.company_id, interview_id=interview.id
    ).model_dump(mode="json")
    outbox.add(session, NOTE_DELETED, data)
