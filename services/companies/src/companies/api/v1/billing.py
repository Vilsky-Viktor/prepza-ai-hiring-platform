from uuid import UUID

from fastapi import APIRouter
from testee_common.auth.auth import CurrentUser
from testee_common.db.paging import PageParams

from companies.schemas.billing import CreditCandidateOut, HistoryEntryOut
from companies.services import credit_history
from companies.services.access import require_editor

# Owners and admins, who top up, see where the credits went and whose invites hold them; viewers
# don't. The company's prices, currency, checkouts, invoices and automatic top-up are billing's
# own routes under the same prefix (the gateway sends them there).
router = APIRouter(prefix="/companies/{company_id}/billing", tags=["companies"])


@router.get("/history")
async def get_history(
    company_id: UUID, user: CurrentUser, page: PageParams
) -> list[HistoryEntryOut]:
    """Every movement of the company's credits, newest first, a page at a time."""
    await require_editor(user, company_id)

    return await credit_history.page(company_id, page.offset, page.limit)


@router.get("/reserved")
async def get_reserved(
    company_id: UUID, user: CurrentUser, page: PageParams
) -> list[CreditCandidateOut]:
    """Candidates invited who haven't finished, whose credits are set aside, newest first."""
    await require_editor(user, company_id)

    return await credit_history.reserved(company_id, page.offset, page.limit)
