from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from library.models.base import Base


class Erasure(Base):
    """An account deleted in the last ERASURE_KEEP_DAYS, the backups' life: a database restored
    or cloned from a backup would bring the person back, so their deletion is run again
    (services/erasures.py). Its email finds them as a candidate. Kept no longer, and never read
    for anything else."""

    __tablename__ = "erasures"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(320))
    erased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
