from prepza_common.config.constants import (
    MAX_CAMPAIGN_BUTTON_LENGTH,
    MAX_CAMPAIGN_SUBJECT_LENGTH,
    MAX_CAMPAIGN_TEXT_LENGTH,
)

from app.helpers.prompts import language_name
from app.prompts.campaigns import CAMPAIGN_TRANSLATION_INPUT
from app.schemas.campaigns import CampaignSource, TranslatedCampaign

LIMITS = {"subject": MAX_CAMPAIGN_SUBJECT_LENGTH, "text": MAX_CAMPAIGN_TEXT_LENGTH}


def campaign_request(source: CampaignSource, language: str) -> str:
    """The user's message of a campaign's translation: its texts, tagged, and the language."""
    return CAMPAIGN_TRANSLATION_INPUT.format(
        language=language_name(language),
        subject=source.subject,
        text=source.text,
        button=source.button or "",
    )


def campaign_limits(source: CampaignSource) -> dict[str, int]:
    """Each field's longest; the button only when the campaign has one."""
    return {**LIMITS, "button": MAX_CAMPAIGN_BUTTON_LENGTH} if source.button else LIMITS


def without_made_up_button(source: CampaignSource, translated: TranslatedCampaign):
    """A campaign without a button gets none, whatever the model wrote."""
    return translated if source.button else translated.model_copy(update={"button": ""})
