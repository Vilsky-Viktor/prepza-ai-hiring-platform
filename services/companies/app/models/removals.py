import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RemovedInvite(Base):
    """A candidate a company erased in the last REMOVAL_KEEP_DAYS, the backups' life: a database
    restored from a backup would bring them back, so the removal is run again
    (services/removal_replay.py). Ids only; never read for anything else."""

    __tablename__ = "removed_invites"

    invite_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    company_id: Mapped[uuid.UUID]
    removed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
