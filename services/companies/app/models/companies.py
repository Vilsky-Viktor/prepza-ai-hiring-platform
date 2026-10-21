import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.roles import Role
from app.constants.verification import MAX_DECLINE_REASON_LENGTH, VerificationStatus
from app.models.base import Base


class Company(Base):
    __tablename__ = "companies"
    # Names are unique across prepza, ignoring case (migration 0012).
    __table_args__ = (Index("uq_companies_lower_name", text("lower(name)"), unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text())
    # The company's logo on candidates' pages, emails and reports: the image itself (small,
    # loaded only when served), its media type, and a version that changes with every upload so
    # its address can be cached for good.
    logo: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)
    logo_type: Mapped[str | None] = mapped_column(String(32))
    logo_version: Mapped[int] = mapped_column(default=0, server_default="0")
    # Its own colors on candidates' pages, by theme ({"light": {...}, "dark": {...}}, each with
    # constants/brand.py's keys as "#rrggbb"); a theme missing: prepza's.
    brand_colors: Mapped[dict | None] = mapped_column(JSONB)
    # Its font, and its cards' and buttons' corner rounding (px), on those pages; None: prepza's.
    brand_font: Mapped[str | None] = mapped_column(String(32))
    brand_radius: Mapped[int | None] = mapped_column(SmallInteger)
    brand_button_radius: Mapped[int | None] = mapped_column(SmallInteger)
    # Verification: the website's domain an owner or admin gave, and the same domain once a
    # superadmin approved it (the badge). Before that, one of them proves the domain with a
    # verified email on it (`verification_email`), which sends the company's name
    # (`verification_name`) for review; the superadmin's decision is kept with it.
    website_domain: Mapped[str | None] = mapped_column(String(253))
    verified_domain: Mapped[str | None] = mapped_column(String(253))
    verification_status: Mapped[str] = mapped_column(
        String(16), default=VerificationStatus.NONE, server_default=VerificationStatus.NONE
    )
    verification_email: Mapped[str | None] = mapped_column(String(320))
    verification_name: Mapped[str | None] = mapped_column(Text())
    verification_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decline_reason: Mapped[str | None] = mapped_column(String(MAX_DECLINE_REASON_LENGTH))
    verification_decided_by: Mapped[str | None] = mapped_column(String(128))
    verification_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    # A superadmin suspended it (impersonation, abuse): nothing new happens until it's lifted.
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Since when members may not use its data from AI apps they connected (None: they may); its
    # owners and admins decide.
    ai_apps_off_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The data processing agreement's version in force when it was made (None before they were
    # recorded): its owner accepted it with the terms. Later versions apply after their notice.
    dpa_version: Mapped[str | None] = mapped_column(String(10))

    members: Mapped[list["Member"]] = relationship(cascade="all, delete-orphan")


class Member(Base):
    """A company owner or admin. Invited admins bind to a user_id when they accept."""

    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("company_id", "invited_email"),
        # Invites to an address across companies (support's lookup).
        Index("ix_members_invited_email", "invited_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    user_id: Mapped[str | None] = mapped_column(String(128), index=True)
    invited_email: Mapped[str] = mapped_column(String(320))
    token: Mapped[str | None] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(32), default=Role.ADMIN)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
