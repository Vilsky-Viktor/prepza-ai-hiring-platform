from testee_common.http import http
from testee_common.http.http import bearer

from assistant.config import settings
from assistant.core.security import service_token


async def company_ids(user_id: str) -> list[str]:
    """Every company the user belongs to, however many, as companies lists them for services;
    raises when companies doesn't answer."""
    response = await http.get_client().get(
        f"{settings.companies_url}/internal/users/{user_id}/companies",
        headers=bearer(service_token("companies")),
    )
    response.raise_for_status()

    return response.json()["company_ids"]
