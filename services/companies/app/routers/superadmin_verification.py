from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.paging import PageParams

from app.constants.verification import REQUEST_CHANGED
from app.helpers.notifications import verification_decided
from app.schemas.verification import ApproveIn, DeclineIn, VerificationRequestOut
from app.services import outbox as outbox_service
from app.storage import companies, verification

# The superadmin reviews companies whose domain a work email proved; everyone else gets "not
# found".
router = APIRouter(prefix="/superadmin/verifications", tags=["superadmin"])


@router.get("")
async def list_requests(
    superadmin: SuperadminUser, page: PageParams
) -> list[VerificationRequestOut]:
    """Pending requests first, then those decided."""
    rows = await verification.requests(page.offset, page.limit)

    return [
        VerificationRequestOut(
            company_id=row.id,
            name=row.verification_name or row.name,
            domain=row.website_domain,
            email=row.verification_email,
            status=row.verification_status,
            submitted_at=row.verification_submitted_at,
            decided_at=row.verification_decided_at,
            decline_reason=row.decline_reason,
        )
        for row in rows
    ]


async def decide(
    company_id: UUID,
    approved: bool,
    superadmin_id: str,
    reason: str | None,
    seen: tuple[str, str] | None = None,
) -> None:
    """Approving gives the company its badge; either way its owners and admins are told. 409
    when the request was decided or changed since the superadmin saw it."""
    company = await companies.get(company_id)

    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    notices = verification_decided(company, approved, reason)

    if not await verification.decide(company_id, approved, superadmin_id, reason, notices, seen):
        raise HTTPException(status.HTTP_409_CONFLICT, REQUEST_CHANGED)

    await outbox_service.flush_quietly()


@router.post("/{company_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
async def approve(company_id: UUID, body: ApproveIn, superadmin: SuperadminUser) -> None:
    """Only the name and domain the superadmin reviewed: a rename since sends it back."""
    await decide(company_id, True, superadmin.uid, None, (body.name, body.domain))


@router.post("/{company_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline(company_id: UUID, body: DeclineIn, superadmin: SuperadminUser) -> None:
    await decide(company_id, False, superadmin.uid, body.reason.strip() or None)
