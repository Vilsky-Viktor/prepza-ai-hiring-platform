import uuid
from datetime import UTC, datetime

from prepza_common.config.constants import MAX_NOTE_LENGTH
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from companies.models.base import Base


class InterviewNote(Base):
    """A note a member wrote on an interview, for its team only. It goes with the interview and
    the company; a member who leaves (or deletes their account) leaves their notes behind,
    shown as a former member's (author_member_id becomes null). An API key writes as itself."""

    __tablename__ = "interview_notes"
    __table_args__ = (
        # An interview's notes, newest first.
        Index("ix_interview_notes_interview_created", "interview_id", "created_at"),
        # At most one pinned note an interview.
        Index(
            "uq_interview_notes_pinned",
            "interview_id",
            unique=True,
            postgresql_where=text("pinned"),
        ),
        CheckConstraint(
            f"char_length(text) BETWEEN 1 AND {MAX_NOTE_LENGTH}", name="ck_interview_notes_text"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"))
    author_member_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"), index=True
    )
    # The API key that wrote it (the api service's), which acts as itself; None for a member's.
    author_key_id: Mapped[uuid.UUID | None]
    text: Mapped[str] = mapped_column(Text)
    pinned: Mapped[bool] = mapped_column(default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    # When its text last changed; None until it's edited.
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
