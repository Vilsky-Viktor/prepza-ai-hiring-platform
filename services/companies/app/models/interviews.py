import uuid
from datetime import UTC, datetime

from prepza_common.constants import DEFAULT_LANGUAGE
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.interviews import DEFAULT_PASS_MARK
from app.models.base import Base


class Interview(Base):
    __tablename__ = "interviews"
    # A company's interviews by last change, for the public API's updated_since (migration 0045).
    __table_args__ = (
        Index("ix_interviews_company_updated", "company_id", "updated_at", "id"),
        # The reminder emails' interviews, by when they got their questions or were started.
        Index("ix_interviews_ready_at", "ready_at"),
        Index("ix_interviews_created_at", "created_at"),
        # Named before the naming convention (models/base.py).
        UniqueConstraint("link_token", name="uq_interviews_link_token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    set_id: Mapped[uuid.UUID | None]
    # Copied from the generated set (and renames), so pages don't ask library for it.
    title: Mapped[str | None] = mapped_column(Text)
    # None for a test made from a template, which needs no generation.
    generation_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    # Its generation failed (generation's generation.failed event); a retry or the questions
    # arriving clear it.
    generation_failed: Mapped[bool] = mapped_column(default=False, server_default="false")
    # When it got its questions (one from a template, when made): a reminder to invite
    # candidates counts from it. None while it has none.
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # What the interview is generated in, as its set in library; invites are emailed in it.
    language: Mapped[str] = mapped_column(String(8), default=DEFAULT_LANGUAGE)
    # The company marked the test as hired; it stays usable.
    hired: Mapped[bool] = mapped_column(default=False)
    # The grade, in percent, a finished candidate needs to pass.
    pass_mark: Mapped[int] = mapped_column(
        default=DEFAULT_PASS_MARK, server_default=str(DEFAULT_PASS_MARK)
    )
    # The shareable link's code while it's on: anyone who opens it can take the test.
    link_token: Mapped[str | None] = mapped_column(String(64))
    # Every interview is timed: each question has question_seconds, and one left unanswered is
    # wrong. Candidates never see their scores. A new test gets its level's (storage/interviews.py);
    # the database's default is from before tests had them.
    question_seconds: Mapped[int] = mapped_column(server_default="60")
    topic_limits: Mapped[dict[str, int]] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    # When the row last changed: a trigger sets it on every update (migration 0045), so the
    # public API's lists can be synced with updated_since.
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
