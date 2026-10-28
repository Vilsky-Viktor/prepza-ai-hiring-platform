from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.verification import FREE_DOMAIN, NOT_A_WEBSITE
from companies.helpers.verification import is_free_domain, website_domain
from companies.repositories import audit, companies, verification
from companies.schemas.verification import VerificationOut, WebsiteIn
from companies.services.access import require_editor
from companies.services.verification import save_website

# Verified companies: an owner or admin gives the website and proves its domain with a verified
# email on it (free mail services never count); a superadmin then reviews the company, and only
# an approved one shows the badge. The superadmin's side is in superadmin_verification.py.
router = APIRouter(prefix="/companies", tags=["verification"])


@router.put("/{company_id}/website")
async def set_website(company_id: UUID, body: WebsiteIn, user: CurrentUser) -> VerificationOut:
    company, _ = await require_editor(user, company_id)

    if not body.website.strip():
        await verification.set_website(company.id, None, None)
    else:
        domain = website_domain(body.website)

        if domain is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOT_A_WEBSITE)

        if is_free_domain(domain):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, FREE_DOMAIN)

        await save_website(company, user, domain)
        await audit.record(
            company.id,
            user.uid,
            AuditAction.VERIFICATION_REQUESTED,
            company.id,
            target_kind=TargetKind.COMPANY,
            target_label=domain,
        )

    saved = await companies.get(company.id)

    return VerificationOut(
        website_domain=saved.website_domain,
        verified_domain=saved.verified_domain,
        verification_status=saved.verification_status,
        decline_reason=saved.decline_reason,
    )
