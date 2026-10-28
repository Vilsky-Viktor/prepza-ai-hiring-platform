from datetime import UTC, datetime

from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from notifications.constants.bulk import SuppressionReason
from notifications.models.base import Base


class SuppressedAddress(Base):
    """An address that bounced for good or marked an email as spam: bulk sends skip it. Kept as
    its keyed hash (helpers/unsubscribe.py address_hash), never in the clear, until a superadmin
    removes it."""

    __tablename__ = "suppressed_addresses"
    __table_args__ = (
        CheckConstraint(one_of("reason", SuppressionReason), name="ck_suppressed_addresses_reason"),
    )

    address: Mapped[str] = mapped_column(String(64), primary_key=True)
    # constants/bulk.py SuppressionReason.
    reason: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
