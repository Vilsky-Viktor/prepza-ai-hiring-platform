from datetime import UTC, datetime

from sqlalchemy import DateTime, Identity, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SoftBounce(Base):
    """A temporary bounce of an email to an address: enough of them within SOFT_BOUNCE_DAYS
    (constants/suppression.py) suppress it. Kept as the address's keyed hash, never in the clear,
    once per email (Resend's id), so a repeated web hook counts once; forgotten after
    SOFT_BOUNCE_DAYS."""

    __tablename__ = "soft_bounces"
    __table_args__ = (UniqueConstraint("address", "email_id"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    address: Mapped[str] = mapped_column(String(64))
    email_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )
