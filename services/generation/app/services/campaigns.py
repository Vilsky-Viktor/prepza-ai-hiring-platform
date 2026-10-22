from uuid import UUID

from prepza_common.constants import (
    MAX_CAMPAIGN_BUTTON_LENGTH,
    MAX_CAMPAIGN_SUBJECT_LENGTH,
    MAX_CAMPAIGN_TEXT_LENGTH,
)

from app.constants.actions import CAMPAIGN_TRANSLATION
from app.helpers.prompts import language_name
from app.integrations import notifications
from app.integrations.usage import ai_run
from app.prompts.campaigns import CAMPAIGN_TRANSLATION_INPUT, CAMPAIGN_TRANSLATION_SYSTEM
from app.schemas.campaigns import CampaignSource, TranslatedCampaign
from app.services.translations import translate_fields, translate_missing

LIMITS = {"subject": MAX_CAMPAIGN_SUBJECT_LENGTH, "text": MAX_CAMPAIGN_TEXT_LENGTH}


async def translate_one(source: CampaignSource, language: str) -> TranslatedCampaign:
    """The campaign in `language`; raises when the model fails or writes past its limits. A
    campaign without a button gets none."""
    request = CAMPAIGN_TRANSLATION_INPUT.format(
        language=language_name(language),
        subject=source.subject,
        text=source.text,
        button=source.button or "",
    )
    limits = {**LIMITS, "button": MAX_CAMPAIGN_BUTTON_LENGTH} if source.button else LIMITS
    translated = await translate_fields(
        TranslatedCampaign, CAMPAIGN_TRANSLATION_SYSTEM, request, limits, language
    )

    return translated if source.button else translated.model_copy(update={"button": ""})


async def translate_campaign(campaign_id: UUID) -> None:
    """Translates the campaign into each language it lacks and saves those that worked; raises
    when a language failed, so the job runs again. Nothing once it's sent or deleted."""
    source = await notifications.get_campaign_source(campaign_id)

    if source is None or not source.missing:
        return

    async def save(done: dict[str, TranslatedCampaign]) -> None:
        await notifications.save_campaign_translations(campaign_id, source, done)

    async with ai_run(CAMPAIGN_TRANSLATION, subject_id=campaign_id):
        await translate_missing(
            f"campaign {campaign_id}",
            source.missing,
            lambda language: translate_one(source, language),
            save,
        )
