from prepza_common.http import http
from prepza_common.http.http import bearer

from app.config.settings import settings
from app.integrations.batches import post_ids
from app.service_auth import service_token


async def statuses(generation_ids: list[str]) -> list[dict]:
    """Each of those generations that still exists: {"id", "status", "owner_uid",
    "updated_at"}."""
    url = f"{settings.generation_url}/internal/generations/statuses"

    return await post_ids(url, service_token("generation"), "ids", generation_ids, "generations")


async def translate_campaign(campaign_id: str) -> None:
    """Queues the campaign's translation into every language it lacks; raises if generation
    can't."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/campaigns/{campaign_id}/translate",
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()
