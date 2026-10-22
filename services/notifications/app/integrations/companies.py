from datetime import datetime

from prepza_common import company_access, http
from prepza_common.http import bearer

from app.config.settings import settings
from app.integrations.batches import post_ids
from app.service_auth import service_token


async def invite_undelivered(invite_id: str) -> None:
    response = await http.get_client().post(
        f"{settings.companies_url}/internal/invites/{invite_id}/undelivered",
        headers=bearer(service_token("companies")),
    )

    response.raise_for_status()


async def company_ids(user_id: str) -> list[str]:
    """Every company the user belongs to: they see its notifications too."""
    response = await http.get_client().get(
        f"{settings.companies_url}/internal/users/{user_id}/companies",
        headers=bearer(service_token("companies")),
    )

    response.raise_for_status()

    return response.json()["company_ids"]


async def invited_company_ids(email: str) -> list[str]:
    """The companies that invited the address; it goes in the body, which request logs don't
    record."""
    response = await http.get_client().post(
        f"{settings.companies_url}/internal/invites/companies",
        json={"email": email},
        headers=bearer(service_token("companies")),
    )

    response.raise_for_status()

    return response.json()["company_ids"]


async def access(company_id: str, user_id: str) -> dict:
    """What the user may do in the company; a company that's gone is no access."""
    return await company_access.access(
        settings.companies_url, service_token("companies"), company_id, user_id
    )


async def require(company_id, user_id: str, editor: bool = False) -> None:
    """A member may look; only an editor (owner or admin) may change. Otherwise a 404, as if
    the company weren't there, or a 403 for a viewer changing."""
    company_access.require(await access(company_id, user_id), editor)


async def members(company_ids: list[str]) -> list[dict]:
    """The companies of those ids that still exist: {"id", "name", "members": [{"user_id",
    "editor"}]}, an editor being an owner or admin."""
    url = f"{settings.companies_url}/internal/companies/members"

    return await post_ids(url, service_token("companies"), "company_ids", company_ids, "companies")


async def waiting_interviews(ready: tuple[datetime, datetime], started: tuple[datetime, datetime]):
    """Interviews ready within `ready` (after, before) that nobody was invited to, and
    interviews started within `started` still waiting for their questions."""
    response = await http.get_client().get(
        f"{settings.companies_url}/internal/interviews/waiting",
        params={
            "ready_after": ready[0].isoformat(),
            "ready_before": ready[1].isoformat(),
            "started_after": started[0].isoformat(),
            "started_before": started[1].isoformat(),
        },
        headers=bearer(service_token("companies")),
    )

    response.raise_for_status()

    return response.json()


async def editor_ids(after: str) -> list[str]:
    """A page of the owners and admins of every company, the ids after `after` in order
    (prepza_common.paging), for a notice about the data processing agreement."""
    response = await http.get_client().get(
        f"{settings.companies_url}/internal/companies/editors",
        params={"after": after},
        headers=bearer(service_token("companies")),
    )
    response.raise_for_status()

    return response.json()["user_ids"]
