from fastapi import status
from testee_common.http import http
from testee_common.http.http import bearer

from notifications.config import settings
from notifications.core.security import service_token


async def news_titles(news_ids: list[str], language: str) -> dict[str, str]:
    """The posts' titles in `language` (English until translated), by id; deleted ones are
    left out."""
    response = await http.get_client().post(
        f"{settings.site_service_url}/internal/news/titles",
        json={"news_ids": news_ids, "language": language},
        headers=bearer(service_token("site")),
    )

    response.raise_for_status()

    return response.json()["titles"]


async def news_post(news_id: str) -> dict | None:
    """A news post's English title and text; None once it's deleted."""
    response = await http.get_client().get(
        f"{settings.site_service_url}/internal/news/{news_id}",
        headers=bearer(service_token("site")),
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()
