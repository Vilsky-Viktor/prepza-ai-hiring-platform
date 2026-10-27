import uuid
from datetime import UTC, datetime
from typing import get_args

from prepza_common.config.constants import MAX_CAMPAIGN_BUTTON_LENGTH, MAX_CAMPAIGN_SUBJECT_LENGTH
from prepza_common.db.db import one_of
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.campaigns import MAX_NOTICE_COMPANIES, AudienceGroup
from app.models.base import Base
from app.schemas.campaigns import CampaignKind

GROUPS = ", ".join(f"'{group}'" for group in AudienceGroup)


def now() -> datetime:
    return datetime.now(UTC)


class Campaign(Base):
    """A product update or an offer to the users who chose it, or an important notice to everyone
    it concerns (constants/bulk.py BulkKind), written by a superadmin in English and translated.
    It goes to everyone, or to the people in its `groups` (constants/campaigns.py
    AudienceGroup); of companies, with `editors_only` only their owners and admins, and for a
    notice with `company_ids` only those companies'. Changeable until it's sent (`sent_at`), then
    its bulk send (about its id) goes out."""

    __tablename__ = "campaigns"
    __table_args__ = (
        CheckConstraint(one_of("kind", get_args(CampaignKind)), name="ck_campaigns_kind"),
        CheckConstraint(f"groups <@ ARRAY[{GROUPS}]::varchar[]", name="ck_campaigns_groups"),
        CheckConstraint(
            "NOT editors_only OR 'members' = ANY (groups)", name="ck_campaigns_editors_only"
        ),
        CheckConstraint(
            f"cardinality(company_ids) <= {MAX_NOTICE_COMPANIES} AND (cardinality(company_ids) = 0"
            " OR (kind = 'notices' AND 'members' = ANY (groups)))",
            name="ck_campaigns_company_ids",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kind: Mapped[str] = mapped_column(String(16))
    # The button's page on the site ("/news#…"); without one, the button opens the site.
    link: Mapped[str | None] = mapped_column(String(300))
    # Empty: everyone (with the setting on, for an optional kind).
    groups: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=list, server_default="{}")
    editors_only: Mapped[bool] = mapped_column(default=False, server_default="false")
    company_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid()), default=list, server_default="{}"
    )
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
