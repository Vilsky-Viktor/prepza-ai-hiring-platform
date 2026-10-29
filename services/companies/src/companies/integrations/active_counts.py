import logging
from uuid import UUID

import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from companies.config import settings
from companies.constants.menu_counts import MENU_COUNT_TIMEOUT_SECONDS
from companies.core.security import service_token

logger = logging.getLogger(__name__)


async def _count(callee: str, url: str, company_id: UUID) -> int | None:
    """The `{count}` a service's internal route gives; None when it didn't answer in time."""
    try:
        response = await http.get_client().get(
            url, headers=bearer(service_token(callee)), timeout=MENU_COUNT_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.warning("No integration count from %s for company %s", callee, company_id)

        return None

    return response.json()["count"]


async def ats_count(company_id: UUID) -> int | None:
    """The company's ATSs connected and working."""
    url = f"{settings.ats_url}/internal/companies/{company_id}/active-count"

    return await _count("ats", url, company_id)


async def slack_count(company_id: UUID) -> int | None:
    """1 while the company's Slack channel is connected and working."""
    url = f"{settings.notifications_url}/internal/companies/{company_id}/active-count"

    return await _count("notifications", url, company_id)


async def api_count(company_id: UUID) -> int | None:
    """The company's API keys that still work and web hooks that get its events."""
    url = f"{settings.api_url}/internal/companies/{company_id}/active-count"

    return await _count("api", url, company_id)


async def ai_apps_count(user_id: str, company_id: UUID) -> int | None:
    """The AI apps the user connected (theirs, not the company's), still connected."""
    url = f"{settings.assistant_url}/internal/users/{user_id}/active-count"

    return await _count("assistant", url, company_id)
