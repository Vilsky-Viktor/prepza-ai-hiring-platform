from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from notifications.models.base import Base


class PendingNote(Base):
    """A note written in the last PENDING_NOTE_HOURS (constants/notes.py), as the activity digest
    tells it: its interview, its author (to leave out of their own digest, and to name) and the
    start of its text. A deleted note, interview or company takes it; a deleted account leaves it
    without its author; older rows go each morning."""

    __tablename__ = "pending_notes"
    __table_args__ = (
        Index("ix_pending_notes_company_created", "company_id", "created_at"),
        Index("ix_pending_notes_interview", "interview_id"),
    )

    note_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    company_id: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    interview_id: Mapped[str] = mapped_column(Uuid(as_uuid=False))
    title: Mapped[str | None] = mapped_column(Text)
    # A user's id or `key:<id>`, and the name the team sees; None once the author's account went.
    author_id: Mapped[str | None] = mapped_column(String(128))
    author_name: Mapped[str | None] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(Text)
    # When the note was written (companies'), which decides whose digest it's in, and when its
    # text last changed (the newest edit wins, whatever order the events come in).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
