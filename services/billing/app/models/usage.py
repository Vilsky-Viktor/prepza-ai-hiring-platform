import uuid
from datetime import datetime
from decimal import Decimal

from prepza_common.ai.ai_constants import ACTIONS, Category, Outcome
from prepza_common.db.db import one_of
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AiUsage(Base):
    """One AI call (or one generation run's calls of a model), as its service recorded it.
    `category` is who it was for, decided here when it's stored: paid, unpaid, no_company or
    prepza. Kept 13 months; a deleted account's id is emptied, and a deleted company's, keeping
    the cost."""

    __tablename__ = "ai_usage"
    __table_args__ = (
        Index("ix_ai_usage_occurred_at", "occurred_at"),
        CheckConstraint(one_of("action", sorted(ACTIONS)), name="ck_ai_usage_action"),
        CheckConstraint(
            one_of("service", sorted(set(ACTIONS.values()))), name="ck_ai_usage_service"
        ),
        CheckConstraint(one_of("outcome", Outcome), name="ck_ai_usage_outcome"),
        CheckConstraint(one_of("category", Category), name="ck_ai_usage_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # The event's id: a redelivered event finds it and adds nothing.
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    action: Mapped[str] = mapped_column(String(48))
    service: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(Text())
    input_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    cached_input_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    output_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    audio_seconds: Mapped[float] = mapped_column(Float, default=0)
    # What it cost in USD, exact: a float's sums of fractions of a cent drift.
    cost: Mapped[Decimal] = mapped_column(Numeric(20, 12), default=0)
    # The company (its uuid, read as text like the services send it).
    company_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), index=True)
    user_id: Mapped[str | None] = mapped_column(String(128), index=True)
    # The generation, conversation or question it was for.
    subject_id: Mapped[str | None] = mapped_column(String(128))
    outcome: Mapped[str] = mapped_column(String(16))
    category: Mapped[str] = mapped_column(String(16))


class LimitHit(Base):
    """One refusal by a limit, ours ("ours") or a provider's ("provider:<name>"). Kept 13 months;
    never an IP."""

    __tablename__ = "limit_hits"
    __table_args__ = (Index("ix_limit_hits_occurred_at", "occurred_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(128), unique=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    limit: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(48))
    # user, company, ip or everyone.
    scope: Mapped[str] = mapped_column(String(16))
    company_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), index=True)
    user_id: Mapped[str | None] = mapped_column(String(128), index=True)
    # What was refused, when the limit says it (the pause's refusals).
    what: Mapped[str | None] = mapped_column(Text())
