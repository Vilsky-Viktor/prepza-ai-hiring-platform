import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InterviewResult(Base):
    """An interview's finished candidates counted for its pass rate: kept by triggers on
    candidate_invites and interviews.pass_mark (migration 0060), in the same transaction as each
    change, so the admin zone's pass rates read them instead of counting every invite."""

    __tablename__ = "interview_results"
    __table_args__ = (
        CheckConstraint(
            "passed >= 0 AND passed <= finished AND grade_total >= 0",
            name="ck_interview_results_counts",
        ),
        # The list by most finished.
        Index("ix_interview_results_finished", text("finished DESC"), "interview_id"),
    )

    interview_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), primary_key=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    # Candidates finished with a grade; of them, at or above the pass mark; their grades added.
    finished: Mapped[int] = mapped_column(BigInteger, server_default="0")
    passed: Mapped[int] = mapped_column(BigInteger, server_default="0")
    grade_total: Mapped[int] = mapped_column(BigInteger, server_default="0")
