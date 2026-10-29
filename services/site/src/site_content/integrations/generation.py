from uuid import UUID

from prepza_common.http import http
from prepza_common.http.http import bearer

from site_content.config import settings
from site_content.core.security import service_token


async def translate_news(news_id: UUID, source: dict) -> None:
    """Queues the post's translation into every language it lacks (`source`: its English title
    and text and those languages); raises if generation can't. The translations come back as
    `news.translated`."""
    response = await http.get_client().post(
        f"{settings.generation_url}/internal/news/{news_id}/translate",
        json=source,
        headers=bearer(service_token("generation")),
    )

    response.raise_for_status()
