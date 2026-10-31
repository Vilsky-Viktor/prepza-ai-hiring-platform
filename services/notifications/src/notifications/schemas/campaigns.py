from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints
from testee_common.config.constants import (
    MAX_CAMPAIGN_BUTTON_LENGTH,
    MAX_CAMPAIGN_SUBJECT_LENGTH,
    MAX_CAMPAIGN_TEXT_LENGTH,
)

from notifications.constants.campaigns import MAX_NOTICE_COMPANIES, AudienceGroup

Subject = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_CAMPAIGN_SUBJECT_LENGTH),
]
Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_CAMPAIGN_TEXT_LENGTH)
]
ButtonText = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=MAX_CAMPAIGN_BUTTON_LENGTH)
]
CampaignKind = Literal["updates", "promotions", "notices"]


class CampaignTexts(BaseModel):
    """A campaign in one language: its subject (also the email's heading), its text (in Markdown:
    the editor's bold, italic, links and lists) and its button's text."""

    subject: Subject
    text: Text
    button: ButtonText | None = None


class AudienceIn(BaseModel):
    """Whom a campaign of `kind` goes to: everyone (no `groups`), or the people in any of
    `groups`; of companies, with `editors_only` only their owners and admins, and for an
    important notice with `company_ids` only those companies'."""

    kind: CampaignKind
    groups: list[AudienceGroup] = Field(default=[], max_length=len(AudienceGroup))
    editors_only: bool = False
    company_ids: list[UUID] = Field(default=[], max_length=MAX_NOTICE_COMPANIES)


class CampaignIn(CampaignTexts, AudienceIn):
    """A campaign as a superadmin writes it, in English: a product update, an offer or an
    important notice, whom it goes to, and the page on the site its button opens."""

    link: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None


class SendIn(BaseModel):
    """An important notice is sent only once the superadmin confirms it's about the service
    itself, never a promotion."""

    acknowledged: bool = False


class CampaignCounts(BaseModel):
    pending: int
    sent: int
    skipped: int
    failed: int
    # Turned the campaign's setting off from it, or marked it as spam (complained).
    unsubscribed: int
    complained: int


class CampaignRowOut(BaseModel):
    """A campaign in the list: its English subject, whether every language has its texts, where
    it stands (a draft, being sent, sent to everyone, or stopped) and once it's sent, its
    counts."""

    id: UUID
    kind: CampaignKind
    subject: str
    created_at: datetime
    sent_at: datetime | None
    translated: bool
    status: Literal["draft", "sending", "sent", "stopped"]
    counts: CampaignCounts | None


class CompanyOut(BaseModel):
    id: UUID
    name: str


class CampaignOut(CampaignRowOut):
    link: str | None
    groups: list[AudienceGroup]
    editors_only: bool
    # The companies an important notice goes to, by name; those deleted since are left out.
    companies: list[CompanyOut]
    # By language; a language without texts gets the English.
    texts: dict[str, CampaignTexts]


class RecipientsOut(BaseModel):
    """Who the campaign would reach now: the users of its audience with an address, not
    suppressed, and for an optional kind with its setting on; each once."""

    count: int


class PreviewOut(BaseModel):
    subject: str
    html: str


class CampaignSourceOut(BaseModel):
    """A campaign to translate, sent to generation: its English texts and the languages it lacks."""

    subject: str
    text: str
    button: str | None
    missing: list[str]
