from prepza_common import http
from prepza_common.http import bearer

from app.config.settings import settings
from app.constants.tool_calls import SERVICE_URLS, TOOL_TIMEOUT_SECONDS
from app.service_auth import service_token


async def updates(service: str, path: str, company_ids: list[str], period: tuple) -> dict:
    """A service's updates for get_updates (its internal route): those of these companies
    after the first time and up to the second, as it answers them (`items`, the newest, and
    how many in all where it counts them); raises when it doesn't answer."""
    since, until = period
    response = await http.get_client().post(
        getattr(settings, SERVICE_URLS[service]) + path,
        json={"company_ids": company_ids, "since": since.isoformat(), "until": until.isoformat()},
        headers=bearer(service_token(service)),
        timeout=TOOL_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    return response.json()
