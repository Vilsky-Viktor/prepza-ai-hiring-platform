import uuid
from datetime import UTC, datetime

from prepza_common.constants import MAX_CAMPAIGN_BUTTON_LENGTH, MAX_CAMPAIGN_SUBJECT_LENGTH
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now() -> datetime:
    return datetime.now(UTC)


class Campaign(Base):
    """A product update or an offer to the users who chose it (constants/bulk.py BulkKind), written
    by a superadmin in English and translated. Changeable until it's sent (`sent_at`), then its
    bulk send (about its id) goes out."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(16))
    # The button's page on the site ("/news#…"); without one, the button opens the site.
    link: Mapped[str | None] = mapped_column(String(300))
    created_by: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, server_default=func.now(), index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CampaignText(Base):
    """A campaign in one language: English as written, the others from generation or edited by
    hand. A language without one gets the English. A changed English deletes the others."""

    __tablename__ = "campaign_texts"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True
    )
    language: Mapped[str] = mapped_column(String(8), primary_key=True)
    subject: Mapped[str] = mapped_column(String(MAX_CAMPAIGN_SUBJECT_LENGTH))
    text: Mapped[str] = mapped_column(Text)
    button: Mapped[str | None] = mapped_column(String(MAX_CAMPAIGN_BUTTON_LENGTH))
