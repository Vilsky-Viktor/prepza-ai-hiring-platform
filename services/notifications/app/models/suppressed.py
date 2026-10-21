from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SuppressedAddress(Base):
    """An address that bounced for good or marked an email as spam: bulk sends skip it. Kept as
    its SHA-256 (helpers/unsubscribe.py address_hash), never in the clear, until a superadmin
    removes it."""

    __tablename__ = "suppressed_addresses"

    address: Mapped[str] = mapped_column(String(64), primary_key=True)
    # constants/bulk.py SuppressionReason.
    reason: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
