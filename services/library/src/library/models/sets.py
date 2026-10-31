import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from testee_common.config.constants import DEFAULT_LANGUAGE, LEVELS
from testee_common.db.db import one_of

from library.constants.sets import OwnerType, Pool, SetKind
from library.models.base import Base


class QuestionSet(Base):
    """A generated preparation or company interview: topics with their questions."""

    __tablename__ = "sets"
    # The question bank looks up templates of one level and language (repositories/reuse.py).
    __table_args__ = (
        Index("ix_sets_kind_level_language", "kind", "level", "language"),
        # Named before the naming convention (models/base.py).
        UniqueConstraint("generation_id", name="uq_sets_generation_id"),
        # A company's set has its company; a platform template has none.
        CheckConstraint(
            "(owner_type = 'company') = (company_id IS NOT NULL)", name="ck_sets_company_id"
        ),
        # Templates of the same title, any case, and language: near-duplicates.
        Index(
            "ix_sets_template_titles",
            "language",
            text("lower(title)"),
            postgresql_where=text("kind = 'template'"),
        ),
        UniqueConstraint("slug", name="uq_sets_slug"),
        CheckConstraint(one_of("kind", SetKind), name="ck_sets_kind"),
        CheckConstraint(one_of("owner_type", OwnerType), name="ck_sets_owner_type"),
        CheckConstraint(one_of("level", LEVELS), name="ck_sets_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Null for sets saved before generations were tracked.
    generation_id: Mapped[uuid.UUID | None] = mapped_column()
    kind: Mapped[str] = mapped_column(String(32))
    owner_type: Mapped[str] = mapped_column(String(32))
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    # The company that owns it, filled by the database from owner_id (a trigger); None for a
    # platform template.
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(Text())
    # A template's readable URL part, set once when it's saved and never changed, so its practice
    # page's URL stays the same after a rename; null for other sets.
    slug: Mapped[str | None] = mapped_column(Text())
    source_text: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(32))
    # The language its content was generated in; reuse only mixes sets of one language.
    language: Mapped[str] = mapped_column(String(8), default=DEFAULT_LANGUAGE)
    requirements: Mapped[list] = mapped_column(JSONB)
    # Stored so lists don't count per row; storage/stats.py keeps them up to date.
    topic_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    topics: Mapped[list["Topic"]] = relationship(
        order_by="Topic.position", cascade="all, delete-orphan"
    )


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        # One topic per place in its set; deferred, so a reorder swaps places in one transaction.
        UniqueConstraint(
            "set_id",
            "position",
            name="uq_topics_set_position",
            deferrable=True,
            initially="DEFERRED",
        ),
        # The topics the embedding job hasn't reached (topics.embedding is outside the models).
        Index("ix_topics_without_embedding", "id", postgresql_where=text("embedding IS NULL")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sets.id", ondelete="CASCADE"), index=True)
    # Its company, filled by the database from sets (a trigger; templates have none).
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    position: Mapped[int]
    title: Mapped[str] = mapped_column(Text)
    subtopics: Mapped[list] = mapped_column(JSONB)

    questions: Mapped[list["Question"]] = relationship(
        order_by="Question.position", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(one_of("pool", Pool), name="ck_questions_pool"),
        # One question per place in its topic; deferred, so a reorder swaps places.
        UniqueConstraint(
            "topic_id",
            "position",
            name="uq_questions_topic_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    # Its company, filled by the database from topics (a trigger; templates have none).
    company_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    position: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSONB)
    # A template question's pool (constants/sets.py Pool), fixed when it's created; none for a
    # company interview's own questions.
    pool: Mapped[str | None] = mapped_column(String(16))
    # The bank's old stages, replaced by `pool` (migration 0027) and no longer read or written;
    # kept for a rollback's older code, and dropped in a later release.
    stage: Mapped[str] = mapped_column(String(16), default="private")
    # A company test's copy of a bank question: its answers count for the original too.
    source_question_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL"), index=True
    )
    # A company test's copy of a shared bank question (bank_questions.id). Not a foreign key on
    # purpose: the mark outlives the bank copy, so a copy never joins the bank in its source's
    # place (after an opt-out or a flag took the source out).
    bank_question_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
