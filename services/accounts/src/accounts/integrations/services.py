from prepza_common.http import http
from prepza_common.http.http import bearer

from accounts.config import settings
from accounts.constants.accounts import ACCOUNT_CALL_TIMEOUT_SECONDS
from accounts.core.security import service_token


def services() -> dict[str, str]:
    """The services that hold their own part of a user's data, by name; companies first, as it
    may refuse a deletion (services/deletion.py)."""
    return {
        "companies": settings.companies_url,
        "rounds": settings.rounds_url,
        "generation": settings.generation_url,
        "billing": settings.billing_url,
        "notifications": settings.notifications_url,
        "ats": settings.ats_url,
        "api": settings.api_url,
        "assistant": settings.assistant_url,
        "library": settings.library_url,
        "site": settings.site_service_url,
    }


async def delete_user(service: str, user_id: str, email: str) -> None:
    """Deletes the user's data in one service; raises if it can't, so deletion can be retried."""
    # The email goes in the body, never the query string, which request logs record.
    response = await http.get_client().request(
        "DELETE",
        f"{services()[service]}/internal/users/{user_id}",
        json={"email": email},
        headers=bearer(service_token(service)),
        timeout=ACCOUNT_CALL_TIMEOUT_SECONDS,
    )

    response.raise_for_status()


async def export_user(service: str, user_id: str, email: str) -> dict:
    response = await http.get_client().post(
        f"{services()[service]}/internal/users/{user_id}/export",
        json={"email": email},
        headers=bearer(service_token(service)),
        timeout=ACCOUNT_CALL_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    return response.json()
