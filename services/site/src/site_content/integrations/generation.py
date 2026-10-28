from uuid import UUID

from prepza_common.http import http
from prepza_common.http.http import bearer

from site_content.config import settings
from site_content.core.security import service_token


async def translate_news(news_id: UUID) -> None:
    """Queues the post's translation into every language it lacks; raises if generation can't."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/news/{news_id}/translate",
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()
