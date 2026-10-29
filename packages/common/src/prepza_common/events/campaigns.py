"""The payload of `notification.campaign_translated`: generation translated a campaign's texts
(its outbox, from the batch that translated them) and notifications saves them, only while the
campaign still reads as `subject`, `text` and `button` and isn't sent. In the `notification.`
family, so notifications' subscription takes it with the rest (its filter is near Pub/Sub's 256
bytes). A payload that fails validation can never be handled (dropped by handle_or_drop)."""

from uuid import UUID

from prepza_common.auth.user import Language
from prepza_common.config.constants import (
    MAX_CAMPAIGN_BUTTON_LENGTH,
    MAX_CAMPAIGN_SUBJECT_LENGTH,
    MAX_CAMPAIGN_TEXT_LENGTH,
)
from pydantic import BaseModel, ConfigDict, Field

CAMPAIGN_TRANSLATED = "notification.campaign_translated"


class CampaignTranslation(BaseModel):
    """A campaign in one language; `button` empty or None when it has none."""

    subject: str = Field(min_length=1, max_length=MAX_CAMPAIGN_SUBJECT_LENGTH)
    text: str = Field(min_length=1, max_length=MAX_CAMPAIGN_TEXT_LENGTH)
    button: str | None = Field(default=None, max_length=MAX_CAMPAIGN_BUTTON_LENGTH)


class CampaignTranslated(BaseModel):
    """The English texts the translations are of, and the translations by language."""

    model_config = ConfigDict(extra="ignore")

    campaign_id: UUID
    subject: str
    text: str
    button: str | None
    translations: dict[Language, CampaignTranslation]
