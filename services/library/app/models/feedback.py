import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.feedback import ReportStatus
from app.models.base import Base


class QuestionRating(Base):
    """A thumbs up (1) or down (-1) per user and question."""

    __tablename__ = "question_ratings"

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[int] = mapped_column(SmallInteger)


class QuestionReporter(Base):
    """Who has reported a question, kept when it's replaced: one report per user and question,
    whatever its revision, so the same users can't send it to the verifier again and again."""

    __tablename__ = "question_reporters"

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)


class QuestionReport(Base):
    """At most one report per user and question."""

    __tablename__ = "question_reports"
    __table_args__ = (
        UniqueConstraint("question_id", "user_id", name="uq_question_reports_question_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(128))
    reason: Mapped[str] = mapped_column(String(32))
    comment: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default=ReportStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
