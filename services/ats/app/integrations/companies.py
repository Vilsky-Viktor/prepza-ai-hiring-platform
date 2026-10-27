from uuid import UUID

from fastapi import status
from prepza_common.auth import company_access, company_invites
from prepza_common.http import http
from prepza_common.http.http import bearer

from app.config.settings import settings
from app.service_auth import service_token

# Companies' refusals of an invite that the ATS flow tells apart: no credits, limits, the
# pause, the interview gone, not ready yet, or the member who connected it no longer an editor.
INVITE_REFUSALS = {
    status.HTTP_402_PAYMENT_REQUIRED,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND,
    status.HTTP_409_CONFLICT,
    status.HTTP_429_TOO_MANY_REQUESTS,
    status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _headers() -> dict:
    return bearer(service_token("companies"))


async def access(company_id: UUID, user_id: str) -> dict:
    """What the user may do in the company; a company that's gone is no access."""
    return await company_access.access(
        settings.companies_url, service_token("companies"), company_id, user_id
    )


async def require(company_id, user_id: str, editor: bool = False) -> None:
    """A member may look; only an editor (owner or admin) may change. Otherwise a 404, as if
    the company weren't there, or a 403 for a viewer changing."""
    company_access.require(await access(company_id, user_id), editor)


async def interviews(ids) -> dict[UUID, dict]:
    """The interviews that exist among `ids`, by id: each with its company_id, title, and
    whether its questions are ready."""
    if not ids:
        return {}

    response = await http.get_client().get(
        f"{settings.companies_url}/internal/interviews",
        params={"ids": [str(item) for item in ids]},
        headers=_headers(),
    )

    response.raise_for_status()

    return {UUID(item["id"]): item for item in response.json()}


async def invite(interview_id: UUID, email: str, sender_id: str, name: str | None = None) -> UUID:
    """Invites the candidate to the interview as `sender_id` would, with their name from the ATS
    (companies keeps a name already known), and returns the invite's id.
    A refusal raises an HTTPException with companies' status and reason (INVITE_REFUSALS)."""
    body = {"email": email, "sender_id": sender_id, "name": name}

    invite_id, _ = await company_invites.invite(
        settings.companies_url, service_token("companies"), interview_id, body, INVITE_REFUSALS
    )

    return invite_id
