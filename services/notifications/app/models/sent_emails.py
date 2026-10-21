from datetime import date

from prepza_common.db import one_of
from sqlalchemy import CheckConstraint, Date, Identity, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.member_emails import MemberEmail
from app.models.base import Base


class SentEmail(Base):
    """An email a schedule sent a user (constants/member_emails.py MemberEmail), or one thing a
    reminder was about. `key` is "day:<date>" for the email itself, or "about:<id>" for what a
    reminder named (an interview), so it isn't named again. Unique, and claimed under a lock
    (storage/sent_emails.py), so a re-run or two runs at once never send twice."""

    __tablename__ = "sent_emails"
    __table_args__ = (
        UniqueConstraint("user_id", "kind", "key"),
        CheckConstraint(one_of("kind", MemberEmail), name="ck_sent_emails_kind"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(32))
    key: Mapped[str] = mapped_column(Text())
    sent_on: Mapped[date] = mapped_column(Date, index=True)
