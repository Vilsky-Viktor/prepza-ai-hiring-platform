import uuid
from datetime import UTC, datetime

from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.emails import ConsentBasis, ConsentSource, EmailSetting
from app.models.base import Base


def now() -> datetime:
    return datetime.now(UTC)


class EmailPreferences(Base):
    """Which emails a user wants; a user without a row has the defaults (constants/emails.py).
    Each column is named after its EmailSetting."""

    __tablename__ = "email_preferences"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    candidate_finished: Mapped[bool] = mapped_column(default=True)
    invite_undelivered: Mapped[bool] = mapped_column(default=True)
    ats_not_invited: Mapped[bool] = mapped_column(default=True)
    interview_ready: Mapped[bool] = mapped_column(default=True)
    reminders: Mapped[bool] = mapped_column(default=True)
    updates: Mapped[bool] = mapped_column(default=False)
    promotions: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EmailConsent(Base):
    """One change of one email setting, never edited: the proof of what the user agreed to,
    where, under which wording and when, or which superadmin changed it on their behalf."""

    __tablename__ = "email_consents"
    __table_args__ = (
        CheckConstraint(one_of("setting", EmailSetting), name="ck_email_consents_setting"),
        CheckConstraint(one_of("source", ConsentSource), name="ck_email_consents_source"),
        CheckConstraint(one_of("basis", ConsentBasis), name="ck_email_consents_basis"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    setting: Mapped[str] = mapped_column(String(32))
    granted: Mapped[bool]
    source: Mapped[str] = mapped_column(String(16))
    basis: Mapped[str] = mapped_column(String(16))
    text_version: Mapped[str] = mapped_column(String(16))
    # The superadmin who made the change, for the admin source only.
    changed_by: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now()
    )
