import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, false
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QuestionStats(Base):
    """How a question has been answered, from rounds' answer.recorded and session.scored events."""

    __tablename__ = "question_stats"

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    answers: Mapped[int] = mapped_column(default=0)
    # Points earned: 1 for a right answer, a share of 1 for a multi-answer one partly right.
    correct: Mapped[float] = mapped_column(Float, default=0)
    # Times each option was picked (each one ticked, for a multi-answer question), keyed by its
    # text: {"option text": count}.
    option_picks: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Answers by candidates who scored well on the topic, and by ones who scored poorly, and how
    # many of each were right: a question both get right as often doesn't separate them.
    strong_answers: Mapped[int] = mapped_column(default=0)
    strong_correct: Mapped[float] = mapped_column(Float, default=0)
    weak_answers: Mapped[int] = mapped_column(default=0)
    weak_correct: Mapped[float] = mapped_column(Float, default=0)
    # Times a candidate ran out of time on it.
    timeouts: Mapped[int] = mapped_column(default=0)
    # A QualityFlag while the question waits for the verifier.
    flag: Mapped[str | None] = mapped_column(String(32))
    # The verifier checked the flag and found nothing wrong: not flagged again until replaced.
    kept: Mapped[bool] = mapped_column(default=False)
    # When the flag was set, or last sent to the verifier again (services/quality.py).
    flagged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When it was last newly flagged (no flag before), which its company was told of.
    flag_raised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class QuestionRevision(Base):
    """A question's previous content and everything learned about it, kept when it's replaced."""

    __tablename__ = "question_revisions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSONB)
    answers: Mapped[int]
    correct: Mapped[float] = mapped_column(Float)
    option_picks: Mapped[dict] = mapped_column(JSONB)
    likes: Mapped[int]
    dislikes: Mapped[int]
    # Every report: [{"reason", "comment", "created_at"}].
    reports: Mapped[list] = mapped_column(JSONB)
    # The QualityFlag it had when it was replaced; None for an owner's edit of an unflagged one.
    flag: Mapped[str | None] = mapped_column(String(32))
    # Replaced because it, or the bank question it's an unchanged copy of, was flagged: its
    # company was told it's fixed.
    fixed: Mapped[bool] = mapped_column(default=False, server_default=false())
    replaced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
