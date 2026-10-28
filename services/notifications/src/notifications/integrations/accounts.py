from datetime import datetime

from fastapi import status
from prepza_common.http import http
from prepza_common.http.http import bearer

from notifications.config import settings
from notifications.core.security import service_token
from notifications.integrations.batches import post_ids


async def unsubscribe(user_id: str, email_settings: list[str]) -> None:
    """Turns the user's email settings off, logged as an unsubscribe; safe to repeat."""
    response = await http.get_client().post(
        f"{settings.accounts_url}/internal/users/{user_id}/unsubscribe",
        json={"settings": email_settings},
        headers=bearer(service_token("accounts")),
    )

    response.raise_for_status()


async def recipients(user_ids: list[str]) -> list[dict]:
    """Each user's address, interface language and email preferences: {"user_id", "email",
    "language", "preferences"}; users who are gone are left out."""
    url = f"{settings.accounts_url}/internal/users/email-recipients"

    return await post_ids(url, service_token("accounts"), "user_ids", user_ids, "recipients")


async def user_ids(after: str, setting: str | None = None) -> list[str]:
    """A page of account ids after `after`, in order (prepza_common.db.paging): every account, for
    a notice about the terms or the privacy policy; with a `setting` ("updates", "promotions"),
    the users who have it on, for a campaign."""
    params = {"after": after, "setting": setting} if setting else {"after": after}
    response = await http.get_client().get(
        f"{settings.accounts_url}/internal/users/ids",
        params=params,
        headers=bearer(service_token("accounts")),
    )
    response.raise_for_status()

    return response.json()["user_ids"]


async def with_setting(user_ids: list[str], setting: str) -> list[str]:
    """Those of the users who have the setting on ("updates", "promotions")."""
    url = f"{settings.accounts_url}/internal/users/with-setting"
    token = service_token("accounts")

    return await post_ids(url, token, "user_ids", user_ids, "user_ids", {"setting": setting})


async def account_created(user_id: str) -> datetime | None:
    """When the account was made; None when accounts doesn't know (no account, or Firebase
    doesn't say)."""
    response = await http.get_client().get(
        f"{settings.accounts_url}/internal/accounts/{user_id}",
        headers=bearer(service_token("accounts")),
    )

    if response.status_code == status.HTTP_404_NOT_FOUND:
        return None

    response.raise_for_status()
    created = response.json()["created_at"]

    return datetime.fromisoformat(created) if created else None
