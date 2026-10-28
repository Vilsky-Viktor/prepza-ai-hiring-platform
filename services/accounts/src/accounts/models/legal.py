from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from accounts.models.base import Base


class TermsAcceptance(Base):
    """The terms' version a user accepted by signing up, and when: the proof of what they agreed
    to. Later versions apply after their notice (the terms say so)."""

    __tablename__ = "terms_acceptances"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    version: Mapped[str] = mapped_column(String(10), primary_key=True)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
