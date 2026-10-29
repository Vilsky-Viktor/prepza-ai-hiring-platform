import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from companies.config import settings
from companies.constants.superadmin import ACCOUNT_ID
from companies.core.security import service_token


async def account(user_id: str) -> dict | None:
    """The account with that id ({"user_id", "email", "created_at"}); None when there's none, or
    the text couldn't be an account's id."""
    if not ACCOUNT_ID.fullmatch(user_id):
        return None

    response = await http.get_client().get(
        f"{settings.accounts_url}/internal/accounts/{user_id}",
        headers=bearer(service_token("accounts")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def account_by_email(email: str) -> dict | None:
    """The account signed in with the address, as account() gives it; None when there's none.
    The address goes in the body, which request logs don't record."""
    response = await http.get_client().post(
        f"{settings.accounts_url}/internal/accounts/lookup",
        json={"email": email},
        headers=bearer(service_token("accounts")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def profiles(user_ids: list[str]) -> dict[str, dict]:
    """Each account's name and picture by its id ({"name", "photo_url"}); those gone are left
    out. At most a page of ids (accounts' lookup limit)."""
    if not user_ids:
        return {}

    response = await http.get_client().post(
        f"{settings.accounts_url}/internal/accounts/profiles",
        json={"user_ids": user_ids},
        headers=bearer(service_token("accounts")),
    )
    response.raise_for_status()

    return {item["user_id"]: item for item in response.json()["profiles"]}
