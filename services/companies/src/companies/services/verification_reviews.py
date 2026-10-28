from uuid import UUID

from fastapi import HTTPException, status

from companies.constants.verification import REQUEST_CHANGED
from companies.core.db import Session
from companies.helpers.notifications import verification_decided
from companies.repositories import companies, verification
from companies.services import outbox as outbox_service


async def decide(
    company_id: UUID,
    approved: bool,
    superadmin_id: str,
    reason: str | None,
    seen: tuple[str, str] | None = None,
) -> None:
    """A superadmin's decision: approving gives the company its badge; either way its owners and
    admins are told, in the same save. 409 when the request was decided or changed since the
    superadmin saw it."""
    async with Session() as session:
        company = await companies.get(session, company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    notices = verification_decided(company, approved, reason)

    async with Session.begin() as session:
        decided = await verification.decide(
            session, company_id, approved, superadmin_id, reason, notices, seen
        )

    if not decided:
        raise HTTPException(status.HTTP_409_CONFLICT, REQUEST_CHANGED)

    await outbox_service.flush_quietly()
