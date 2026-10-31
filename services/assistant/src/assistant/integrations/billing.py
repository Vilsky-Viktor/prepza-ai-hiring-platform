from uuid import UUID

import httpx
from testee_common.http import http
from testee_common.http.http import bearer

from assistant.config import settings
from assistant.constants.tool_calls import TOOL_TIMEOUT_SECONDS
from assistant.constants.updates import LOW_COMPANIES_PATH
from assistant.core.security import service_token


async def company_paid(company_id: UUID) -> bool:
    """Whether the company ever topped up. When billing can't say, it counts as not: the turn
    is then held to the limits for everyone, rather than refused."""
    try:
        response = await http.get_client().get(
            f"{settings.billing_url}/internal/companies/{company_id}/paid",
            headers=bearer(service_token("billing")),
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return False

    return response.json()["paid"]


async def low_companies(company_ids: list[str]) -> list[dict]:
    """Those of the companies running low on credits that no automatic top-up refills (as
    billing's reminders tell it), each with the candidates its credits still pay for; raises
    when billing doesn't answer."""
    response = await http.get_client().get(
        settings.billing_url + LOW_COMPANIES_PATH,
        params={"ids": company_ids},
        headers=bearer(service_token("billing")),
        timeout=TOOL_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    return response.json()["companies"]
