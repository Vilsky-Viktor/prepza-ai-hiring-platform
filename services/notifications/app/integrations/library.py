from datetime import datetime

from fastapi import status
from prepza_common import http
from prepza_common.http import bearer
from prepza_common.paging import every_id

from app.config.settings import settings
from app.integrations.batches import post_ids
from app.service_auth import service_token


async def unsubscribe(user_id: str, email_settings: list[str]) -> None:
    """Turns the user's email settings off, logged as an unsubscribe; safe to repeat."""
    response = await http.get_client().post(
        f"{settings.library_url}/internal/users/{user_id}/unsubscribe",
        json={"settings": email_settings},
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()


async def recipients(user_ids: list[str]) -> list[dict]:
    """Each user's address, interface language and email preferences: {"user_id", "email",
    "language", "preferences"}; users who are gone are left out."""
    url = f"{settings.library_url}/internal/users/email-recipients"

    return await post_ids(url, service_token("library"), "user_ids", user_ids, "recipients")


async def user_ids(setting: str | None = None) -> list[str]:
    """Every account, for a notice about the terms or the privacy policy; with a `setting`
    ("updates", "promotions"), the users who have it on, for a campaign, read a page at a
    time."""

    async def read_page(after: str) -> list[str]:
        response = await http.get_client().get(
            f"{settings.library_url}/internal/users/ids",
            params={"setting": setting, "after": after} if setting else None,
            headers=bearer(service_token("library")),
        )
        response.raise_for_status()

        return response.json()["user_ids"]

    if setting is None:
        return await read_page("")

    return await every_id(read_page)


async def account_created(user_id: str) -> datetime | None:
    """When the account was made; None when library doesn't know (no account, or Firebase
    doesn't say)."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/accounts/{user_id}",
        headers=bearer(service_token("library")),
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return None

    response.raise_for_status()
    created = response.json()["created_at"]

    return datetime.fromisoformat(created) if created else None


async def news_titles(news_ids: list[str], language: str) -> dict[str, str]:
    """The posts' titles in `language` (English until translated), by id; deleted ones are
    left out."""
    response = await http.get_client().post(
        f"{settings.library_url}/internal/news/titles",
        json={"news_ids": news_ids, "language": language},
        headers=bearer(service_token("library")),
    )

    response.raise_for_status()

    return response.json()["titles"]


async def news_post(news_id: str) -> dict | None:
    """A news post's English title and text; None once it's deleted."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/news/{news_id}",
        headers=bearer(service_token("library")),
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()
