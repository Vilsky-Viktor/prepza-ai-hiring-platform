"""The shared question bank: companies' proven questions that passed the filter, reused in
other companies' interviews (docs/generation.md, The question bank)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from library.models.base import Base


class BankQuestion(Base):
    """A copy of a company's question in the bank, with no company id: deleting the company, its
    interview or its account never deletes it (its link to the source is only cleared). It
    leaves only when its source's interview is kept private, or it or a copy of it is flagged or
    reported."""

    __tablename__ = "bank_questions"
    # The bank looks up questions of one level and language (repositories/reuse.py).
    __table_args__ = (Index("ix_bank_questions_level_language", "level", "language"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # The company's question it was copied from, kept only so an opt-out or a flag can take it
    # out; cleared, never cascaded, when that question goes. One bank copy per question.
    source_question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL"), unique=True
    )
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSONB)
    level: Mapped[str] = mapped_column(String(32))
    language: Mapped[str] = mapped_column(String(8))
    # bank_questions.embedding, its topic's (a pgvector column outside the models, like
    # topics.embedding), is what reuse matches a new topic against.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BankCheck(Base):
    """The filter's verdict on a company's question, for its wording when checked (`text_hash`,
    md5 of the text): a question changed since is checked again. Goes with its question."""

    __tablename__ = "bank_checks"

    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    # Its company, filled by the database from questions (a trigger).
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    text_hash: Mapped[str] = mapped_column(String(32))
    # Named and revealed nothing about an organisation or a person.
    passed: Mapped[bool]
    # It, or a copy of it, was flagged or reported after it joined: it never joins again.
    barred: Mapped[bool] = mapped_column(default=False, server_default="false")
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewPrivacy(Base):
    """Companies' bank opt-out (`keep_private`) per interview, from interview.privacy_changed:
    its set named by its id or by the generation that saves it, as the set may not exist yet.
    The newest change wins, whatever order the events come in."""

    __tablename__ = "interview_privacy"

    interview_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(index=True)
    set_id: Mapped[uuid.UUID | None]
    generation_id: Mapped[uuid.UUID | None]
    keep_private: Mapped[bool]
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
