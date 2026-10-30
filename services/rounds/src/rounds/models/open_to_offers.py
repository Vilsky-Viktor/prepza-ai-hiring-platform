import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from rounds.models.base import Base


class OpenToOffers(Base):
    """A practice user who chose to be listed on paying companies' Discover tabs, with the
    LinkedIn profile they shared. Deleted when they turn it off, when it lapses (OPEN_DAYS after
    `opened_at`, jobs: open-to-offers) and with their account; then they're on no tab at once."""

    __tablename__ = "open_to_offers"
    __table_args__ = (Index("ix_open_to_offers_opened_at", "opened_at"),)

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    # Their name as their sign-in gave it when they turned it on: shared, never their email.
    name: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str] = mapped_column(Text)
    # When they last turned it on (or changed their profile's address): the lapse counts from it.
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OfferConsent(Base):
    """One change of the Open to offers switch, never edited: the proof of what the person agreed
    to, under which wording and when, or that they withdrew. Deleted with their account."""

    __tablename__ = "offer_consents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    granted: Mapped[bool]
    # The switch's wording they saw (CONSENT_VERSION); None for a withdrawal or a lapse.
    text_version: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
