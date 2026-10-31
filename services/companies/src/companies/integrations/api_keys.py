from uuid import UUID

from testee_common.http import http
from testee_common.http.http import bearer

from companies.config import settings
from companies.core.security import service_token


async def names(company_id: UUID, key_ids: list) -> dict[str, str]:
    """The names the company's API keys with those ids have now, by id (the api service keeps
    them), so a renamed key reads as it's called today; deleted ones are left out."""
    if not key_ids:
        return {}

    response = await http.get_client().get(
        f"{settings.api_url}/internal/companies/{company_id}/keys/names",
        params={"ids": sorted({str(key_id) for key_id in key_ids})},
        headers=bearer(service_token("api")),
    )
    response.raise_for_status()

    return response.json()
