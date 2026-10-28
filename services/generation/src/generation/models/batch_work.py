import uuid
from datetime import datetime

from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, Index, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from generation.constants.batch_work import BatchKind, BatchStep
from generation.models.base import Base


class BatchWork(Base):
    """One piece of work waiting on, or sent in, an OpenAI batch (services/batch_work.py): its
    kind, what it's for (`subject_id`, and `key`: the language of a translation), the call it
    waits on, and what its next step needs (`payload`)."""

    __tablename__ = "batch_work"
    __table_args__ = (
        UniqueConstraint("kind", "subject_id", "key", name="uq_batch_work_kind_subject_id_key"),
        Index("ix_batch_work_unsent", "created_at", postgresql_where=text("batch_id IS NULL")),
        CheckConstraint(one_of("kind", BatchKind), name="ck_batch_work_kind"),
        CheckConstraint(one_of("step", BatchStep), name="ck_batch_work_step"),
        CheckConstraint("attempt >= 0", name="ck_batch_work_attempt"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(Text)
    subject_id: Mapped[uuid.UUID]
    key: Mapped[str] = mapped_column(Text, server_default="")
    step: Mapped[str] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(server_default="0")
    payload: Mapped[dict] = mapped_column(JSONB)
    # The chat completion it waits on, as the batch sends it.
    body: Mapped[dict] = mapped_column(JSONB)
    # Null until sent in a batch.
    batch_id: Mapped[str | None] = mapped_column(Text, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
