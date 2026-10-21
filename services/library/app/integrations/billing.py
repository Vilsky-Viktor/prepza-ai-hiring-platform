import logging

from prepza_common import http
from prepza_common.http import bearer

from app.config.settings import settings
from app.service_auth import service_token

logger = logging.getLogger(__name__)


async def remember_currency(user_id: str, country: str | None) -> None:
    """A new account sees prices in its `country`'s currency until changed. Never fails the
    sign-up: billing also saves it the first time it sees the person with a country."""
    try:
        response = await http.get_client().post(
            f"{settings.billing_url}/internal/users/{user_id}/currency",
            params={"country": country} if country else None,
            headers=bearer(service_token("billing")),
        )
        response.raise_for_status()
    except Exception:
        logger.exception("Couldn't save the new account's currency")
