from uuid import UUID

import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from generation.config import settings
from generation.core.security import service_token
from generation.schemas.news import NewsSource, TranslatedNews


async def get_news_source(news_id: UUID) -> NewsSource | None:
    """A news post's English text and the languages it lacks; None once it's deleted."""
    response = await http.get_client().get(
        f"{settings.site_service_url}/internal/news/{news_id}",
        headers=bearer(service_token("site")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return NewsSource.model_validate(response.json())


async def save_news_translations(
    news_id: UUID, source: NewsSource, translations: dict[str, TranslatedNews]
) -> None:
    """Saves the translations of `source`; site drops them if the post changed since."""
    response = await http.get_client().put(
        f"{settings.site_service_url}/internal/news/{news_id}/translations",
        json={
            "title": source.title,
            "text": source.text,
            "translations": {code: item.model_dump() for code, item in translations.items()},
        },
        headers=bearer(service_token("site")),
    )

    response.raise_for_status()
