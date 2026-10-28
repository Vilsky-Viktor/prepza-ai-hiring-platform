import uuid
from datetime import datetime

from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from generation.constants.patterns import PatternStatus
from generation.constants.quality import QualityFlag
from generation.models.base import Base


class QualityPattern(Base):
    """A recurring mistake in flagged or replaced questions, written as a general rule by the
    weekly pattern job. Only counts and dates of the questions that showed it are kept: never
    their ids or text."""

    __tablename__ = "quality_patterns"
    __table_args__ = (
        CheckConstraint(one_of("flag", QualityFlag), name="ck_quality_patterns_flag"),
        CheckConstraint(one_of("status", PatternStatus), name="ck_quality_patterns_status"),
        CheckConstraint("question_count >= 0", name="ck_quality_patterns_question_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(Text)
    # The QualityFlag of the questions it comes from.
    flag: Mapped[str] = mapped_column(String(32))
    # How many questions showed it, over every run that found it.
    question_count: Mapped[int] = mapped_column(Integer)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(16), default=PatternStatus.PROPOSED, index=True)
    # The superadmin who approved or dismissed it, and when.
    reviewed_by: Mapped[str | None] = mapped_column(String(128))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
