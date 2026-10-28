from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.paging import PageParams

from companies.core.db import Session
from companies.repositories import verification
from companies.schemas.verification import ApproveIn, DeclineIn, VerificationRequestOut
from companies.services import verification_reviews

# The superadmin reviews companies whose domain a work email proved; everyone else gets "not
# found".
router = APIRouter(prefix="/superadmin/verifications", tags=["superadmin"])


@router.get("")
async def list_requests(
    superadmin: SuperadminUser, page: PageParams
) -> list[VerificationRequestOut]:
    """Pending requests first, then those decided."""
    async with Session() as session:
        rows = await verification.requests(session, page.offset, page.limit)

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


@router.post("/{company_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
async def approve(company_id: UUID, body: ApproveIn, superadmin: SuperadminUser) -> None:
    """Only the name and domain the superadmin reviewed: a rename since sends it back."""
    await verification_reviews.decide(
        company_id, True, superadmin.uid, None, (body.name, body.domain)
    )


@router.post("/{company_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline(company_id: UUID, body: DeclineIn, superadmin: SuperadminUser) -> None:
    await verification_reviews.decide(
        company_id, False, superadmin.uid, body.reason.strip() or None
    )
