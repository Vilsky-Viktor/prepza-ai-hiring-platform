from uuid import UUID

import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from generation.config import settings
from generation.core.security import service_token
from generation.schemas.campaigns import CampaignSource, TranslatedCampaign


async def get_campaign_source(campaign_id: UUID) -> CampaignSource | None:
    """A campaign's English texts and the languages it lacks; None once it's deleted."""
    response = await http.get_client().get(
        f"{settings.notifications_url}/internal/campaigns/{campaign_id}",
        headers=bearer(service_token("notifications")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return CampaignSource.model_validate(response.json())


async def save_campaign_translations(
    campaign_id: UUID, source: CampaignSource, translations: dict[str, TranslatedCampaign]
) -> None:
    """Saves the translations of `source`; notifications drops them if it changed since."""
    response = await http.get_client().put(
        f"{settings.notifications_url}/internal/campaigns/{campaign_id}/translations",
        json={
            "subject": source.subject,
            "text": source.text,
            "button": source.button,
            "translations": {code: item.model_dump() for code, item in translations.items()},
        },
        headers=bearer(service_token("notifications")),
    )

    response.raise_for_status()
