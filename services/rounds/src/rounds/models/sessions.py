import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rounds.constants.rounds import CORRECT_SCORE, RoundStatus
from rounds.models.base import Base
from rounds.models.signals import Signal

# For the relationship's annotation only; the class is resolved by name at runtime.
if TYPE_CHECKING:
    from rounds.models.answers import Answer


class Session(Base):
    """One pass by a candidate through an interview topic. Single pass, no reveal."""

    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("candidate_invite_id", "topic_id", name="uq_sessions_invite_topic"),
        Index(
            "ix_sessions_running_invite",
            "candidate_invite_id",
            postgresql_where="status = 'in_progress'",
        ),
        CheckConstraint(one_of("status", RoundStatus), name="ck_sessions_status"),
        CheckConstraint(
            f"final_score BETWEEN 0 AND {CORRECT_SCORE}", name="ck_sessions_final_score"
        ),
        CheckConstraint("question_seconds > 0", name="ck_sessions_question_seconds"),
        # An interview's section has its company; practice has none.
        CheckConstraint("practice OR company_id IS NOT NULL", name="ck_sessions_company_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(index=True)
    interview_set_id: Mapped[uuid.UUID] = mapped_column(index=True)
    # Indexed by uq_sessions_invite_topic's first column.
    candidate_invite_id: Mapped[uuid.UUID] = mapped_column()
    # The interview's company (companies sends it); None for practice.
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    topic_title: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=RoundStatus.IN_PROGRESS)
    questions: Mapped[list] = mapped_column(JSONB)
    final_score: Mapped[int | None]
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The average seconds a question, with the candidate's extra time: each question's own time
    # (`seconds` in `questions`, helpers/question_times.py) is fitted to it, so they add up to
    # this times the questions. None when untimed (a practice round, sessions from before every
    # interview was timed).
    question_seconds: Mapped[int | None]
    # Answers that stay out of the questions' statistics: a company member trying their own test,
    # or a talent's practice round after their first on the template.
    preview: Mapped[bool] = mapped_column(default=False)
    # A talent's free practice round on a template: candidate_invite_id is the round's id, it
    # belongs to no company, and every right answer is shown after it.
    practice: Mapped[bool] = mapped_column(default=False)
    # When the question now waiting for an answer was first shown; cleared by the answer.
    question_shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Voice mode: the interviewer reads each question and its options aloud, and the candidate
    # may answer by voice (the interview's setting in companies).
    voice: Mapped[bool] = mapped_column(default=False, server_default="false")
    # Voice mode: the seconds the question now waiting is read aloud; its own time starts after
    # them. Cleared by the answer, with question_shown_at.
    question_reading_seconds: Mapped[int | None]

    answers: Mapped[list["Answer"]] = relationship(order_by="Answer.created_at")
    signals: Mapped[list[Signal]] = relationship(order_by=Signal.created_at)
