import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from rounds.models.base import Base


class HelpVote(Base):
    """Votes on the help chat's answers from before it moved to the assistant (which keeps them
    now, in its own help_votes). Nothing writes here any more; the next release drops the table
    (expand, then contract)."""

    __tablename__ = "help_votes"
    __table_args__ = (CheckConstraint("vote IN (-1, 1)", name="ck_help_votes_vote"),)

    answer_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # The answer's Langfuse trace; None when Langfuse wasn't set up.
    trace_id: Mapped[str | None] = mapped_column(String(32))
    # 1 (up) or -1 (down); a cleared vote's row is deleted.
    vote: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
