from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth.auth import CurrentUser

from companies.schemas.verification import VerificationOut, WebsiteIn
from companies.services.access import require_editor
from companies.services.verification import change_website

# Verified companies: an owner or admin gives the website and proves its domain with a verified
# email on it (free mail services never count); a superadmin then reviews the company, and only
# an approved one shows the badge. The superadmin's side is in superadmin_verification.py.
router = APIRouter(prefix="/companies", tags=["verification"])


@router.put("/{company_id}/website")
async def set_website(company_id: UUID, body: WebsiteIn, user: CurrentUser) -> VerificationOut:
    company, _ = await require_editor(user, company_id)
    saved = await change_website(company, user, body.website)

    return VerificationOut(
        website_domain=saved.website_domain,
        verified_domain=saved.verified_domain,
        verification_status=saved.verification_status,
        decline_reason=saved.decline_reason,
    )
