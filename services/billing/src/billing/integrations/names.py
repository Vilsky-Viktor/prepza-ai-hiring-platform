"""Names for the AI costs tab's top lists: companies' names (companies) and accounts' emails
(library). Best effort: without an answer, the tab shows the ids."""

import logging

import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from billing.config import settings
from billing.core.security import service_token

logger = logging.getLogger(__name__)


async def company_names(company_ids: list[str]) -> dict[str, str]:
    if not company_ids:
        return {}

    try:
        response = await http.get_client().post(
            f"{settings.companies_url}/internal/companies/members",
            json={"company_ids": company_ids},
            headers=bearer(service_token("companies")),
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.warning("Couldn't get companies' names", exc_info=True)

        return {}

    return {found["id"]: found["name"] for found in response.json()["companies"]}


async def user_emails(user_ids: list[str]) -> dict[str, str]:
    if not user_ids:
        return {}

    try:
        response = await http.get_client().post(
            f"{settings.library_url}/internal/users/email-recipients",
            json={"user_ids": user_ids},
            headers=bearer(service_token("library")),
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.warning("Couldn't get accounts' emails", exc_info=True)

        return {}

    return {found["user_id"]: found["email"] for found in response.json()["recipients"]}
