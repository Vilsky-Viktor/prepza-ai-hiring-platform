from prepza_common.http import http
from prepza_common.http.http import bearer

from notifications.config import settings
from notifications.core.security import service_token
from notifications.integrations.batches import post_ids


async def statuses(generation_ids: list[str]) -> list[dict]:
    """Each of those generations that still exists: {"id", "status", "owner_uid",
    "updated_at"}."""
    url = f"{settings.generation_url}/internal/generations/statuses"

    return await post_ids(url, service_token("generation"), "ids", generation_ids, "generations")


async def translate_campaign(campaign_id: str, source: dict) -> None:
    """Queues the campaign's translation into every language it lacks (`source`: its English
    texts and those languages); raises if generation can't. The translations come back as
    `notification.campaign_translated`."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/campaigns/{campaign_id}/translate",
        json=source,
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()
