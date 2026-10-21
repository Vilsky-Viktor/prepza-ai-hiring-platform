import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.rounds import CORRECT_SCORE
from app.models.base import Base


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_answers_session_question"),
        CheckConstraint(f"score BETWEEN 0 AND {CORRECT_SCORE}", name="ck_answers_score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    question_id: Mapped[uuid.UUID]
    # The option picked on a single-answer question; None for a multi-answer one, and when the
    # time ran out.
    option_index: Mapped[int | None]
    # The options ticked on a multi-answer ("select all that apply") question, in order; None for
    # a single-answer one, and when the time ran out.
    picks: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    # A timed question ran out before the candidate answered: it counts as wrong.
    timed_out: Mapped[bool] = mapped_column(default=False, server_default=false())
    # All points: right, or every right option of a multi-answer question and no wrong one.
    correct: Mapped[bool]
    # Points out of CORRECT_SCORE (helpers/scores.py answer_score), so averages read as percent
    # correct.
    score: Mapped[int]
    # Interview answers only: seconds from the question being shown to it being answered.
    seconds: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
