import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class KeyCheck(Base):
    """A flagged question waiting for its key check in an OpenAI batch."""

    __tablename__ = "key_checks"

    question_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # The text that was flagged; a result for a question changed since then is dropped.
    question_text: Mapped[str] = mapped_column(Text)
    # The option marked correct then; a result for a key moved since is dropped too. None for
    # checks queued before it was kept.
    marked_answer: Mapped[str | None] = mapped_column(Text)
    # Null until sent in a batch.
    batch_id: Mapped[str | None] = mapped_column(Text(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
