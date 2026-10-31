from testee_common.http import http
from testee_common.http.http import bearer

from notifications.config import settings
from notifications.core.security import service_token


async def low_companies() -> list[dict]:
    """Companies running low on credits that no automatic top-up refills: {"company_id",
    "available"}."""
    response = await http.get_client().get(
        f"{settings.billing_url}/internal/companies/low",
        headers=bearer(service_token("billing")),
    )

    response.raise_for_status()

    return response.json()["companies"]
