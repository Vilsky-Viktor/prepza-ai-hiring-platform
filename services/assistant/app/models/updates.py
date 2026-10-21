from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UpdateCheck(Base):
    """When an AI app connection (its grant's id) or an API key (its id) last called
    get_updates: its next call tells what came since. Rows unused for the bell's KEEP_DAYS go
    with the daily retention."""

    __tablename__ = "update_checks"

    connection_id: Mapped[str] = mapped_column(Text(), primary_key=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
