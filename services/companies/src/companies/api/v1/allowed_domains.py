from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth.auth import CurrentUser

from companies.api.dependencies import Via
from companies.schemas.allowed_domains import AllowedDomains
from companies.services import company_settings

router = APIRouter(prefix="/companies/{company_id}/allowed-domains", tags=["companies"])


@router.put("")
async def set_allowed_domains(
    company_id: UUID, body: AllowedDomains, user: CurrentUser, via: Via
) -> AllowedDomains:
    """Owners and admins set the sites that may embed the company's interviews and that the
    API's return_url may lead to, and whether localhost may too; the saved list. Never through
    an AI app or the assistant: a person decides, in prepza itself."""
    return await company_settings.set_allowed_domains(company_id, user, body, via)
