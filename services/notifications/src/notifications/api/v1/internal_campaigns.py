from uuid import UUID

from fastapi import APIRouter, status

from notifications.api.dependencies import ServiceCaller
from notifications.schemas.campaigns import CampaignSourceOut, CampaignTranslationsIn
from notifications.services import campaign_views, campaigns

# Campaigns' translations, written by generation (its translate-campaign job).
router = APIRouter(prefix="/internal/campaigns", tags=["internal"])


@router.get("/{campaign_id}")
async def get_campaign_source(campaign_id: UUID, caller: ServiceCaller) -> CampaignSourceOut:
    """Its English texts and the languages it lacks; none once it's sent."""
    return await campaign_views.source(campaign_id)


@router.put("/{campaign_id}/translations", status_code=status.HTTP_204_NO_CONTENT)
async def save_campaign_translations(
    campaign_id: UUID, body: CampaignTranslationsIn, caller: ServiceCaller
) -> None:
    """Safe to repeat; translations of an older text, or of a campaign sent or deleted since,
    are dropped, and a language edited by hand keeps its wording."""
    english = {"subject": body.subject, "text": body.text, "button": body.button}
    translations = {
        language: {"subject": item.subject, "text": item.text, "button": item.button or None}
        for language, item in body.translations.items()
    }
    await campaigns.save_translations(campaign_id, english, translations)
