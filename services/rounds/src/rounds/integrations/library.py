from uuid import UUID

import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from rounds.config import settings
from rounds.core.security import service_token


async def get_set(set_id: UUID) -> dict | None:
    response = await http.get_client().get(
        f"{settings.library_url}/internal/sets/{set_id}",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()


async def practice_content(template_id: UUID) -> dict | None:
    """A template's revealed questions by topic, with answers; None when there's no template."""
    response = await http.get_client().get(
        f"{settings.library_url}/internal/templates/{template_id}/practice",
        headers=bearer(service_token("library")),
    )

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    response.raise_for_status()

    return response.json()
