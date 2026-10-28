import uuid
from datetime import datetime

from prepza_common.config.constants import DEFAULT_LANGUAGE
from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from generation.constants.kinds import GenerationKind
from generation.constants.statuses import Status
from generation.models.base import Base


class Generation(Base):
    __tablename__ = "generations"
    # One question addition at a time for a template: two at once would both add what's missing.
    __table_args__ = (
        Index(
            "ix_generations_one_addition_per_template",
            "preparation_id",
            unique=True,
            postgresql_where=text(
                "kind = 'template_questions' AND status IN ('queued', 'running')"
            ),
        ),
        # A template's latest addition; the stuck and waiting ones the schedules fail or expire;
        # the finished ones whose pasted text is still kept.
        Index(
            "ix_generations_template_additions",
            "preparation_id",
            "created_at",
            postgresql_where=text("kind = 'template_questions'"),
        ),
        Index(
            "ix_generations_unsettled",
            "updated_at",
            postgresql_where=text("status IN ('queued', 'running', 'awaiting_review')"),
        ),
        Index("ix_generations_text_kept", "updated_at", postgresql_where=text("text <> ''")),
        CheckConstraint(one_of("kind", GenerationKind), name="ck_generations_kind"),
        CheckConstraint(one_of("status", Status), name="ck_generations_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_uid: Mapped[str] = mapped_column(String(128), index=True)
    kind: Mapped[str] = mapped_column(String(32), default="interview")
    company_id: Mapped[uuid.UUID | None]
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), default=DEFAULT_LANGUAGE)
    status: Mapped[str] = mapped_column(String(32), default=Status.QUEUED)
    topics: Mapped[list | None] = mapped_column(JSONB)
    progress: Mapped[dict | None] = mapped_column(JSONB)
    # The set it saved; for a question addition, the template it adds to, from the start.
    preparation_id: Mapped[uuid.UUID | None]
    # The questions a superadmin's addition adds to each topic; none for a top-up, which writes
    # what each topic lacks, and for every other kind.
    question_count: Mapped[int | None]
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
