import uuid
from datetime import datetime

from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from rounds.constants.integrity import IntegritySignal
from rounds.models.base import Base


class Signal(Base):
    """One page leave or copy reported by a candidate's browser, with the question on screen."""

    __tablename__ = "signals"
    __table_args__ = (CheckConstraint(one_of("kind", IntegritySignal), name="ck_signals_kind"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    # The section's company, filled by the database from sessions (a trigger).
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    # None when no question was open, e.g. on an answer's result.
    question_id: Mapped[uuid.UUID | None]
    kind: Mapped[str] = mapped_column(String(32))
    # For a page leave: how long the candidate was away, once they came back.
    away_seconds: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
