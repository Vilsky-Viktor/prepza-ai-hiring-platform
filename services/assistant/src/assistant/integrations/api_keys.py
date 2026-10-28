from fastapi import status
from prepza_common.http import http
from prepza_common.http.http import bearer, passed_on

from assistant.config import settings
from assistant.constants.mcp import VERIFY_KEY_PATH
from assistant.core.security import service_token


async def verify(key: str, ip: str | None) -> dict | None:
    """The api service's check of a company's API key used from `ip`, as the API checks it,
    counted against the company's API limit: its id, company_id, created_by (the member it acts
    as) and permissions. None for a key that doesn't work; the api's 403 for an address the key
    doesn't allow, and over the limit its 429 with its Retry-After."""
    response = await http.get_client().post(
        settings.api_url + VERIFY_KEY_PATH,
        json={"key": key, "ip": ip},
        headers=bearer(service_token("api")),
    )

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        return None

    refusals = {status.HTTP_403_FORBIDDEN, status.HTTP_429_TOO_MANY_REQUESTS}

    return passed_on(response, refusals).json()
