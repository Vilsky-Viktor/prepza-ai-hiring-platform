from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth import CurrentUser
from prepza_common.paging import PageParams

from app.integrations import billing
from app.schemas.billing import (
    CreditCandidateOut,
    HistoryEntryOut,
    InvoiceOut,
    TopUpCheckoutIn,
    TopUpCheckoutOut,
)
from app.services import credit_history
from app.services.access import require_editor

# Owners and admins, who top up, see where the credits went; viewers don't.
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


@router.get("/invoice")
async def get_invoice(company_id: UUID, transaction_id: str, user: CurrentUser) -> InvoiceOut:
    """A temporary link to the invoice of one of the company's top-ups."""
    await require_editor(user, company_id)

    return InvoiceOut(url=await billing.company_invoice(company_id, transaction_id))


@router.post("/checkout")
async def create_checkout(
    company_id: UUID, body: TopUpCheckoutIn, user: CurrentUser
) -> TopUpCheckoutOut:
    """A Paddle checkout for a top-up of some number of candidates, paid by the user into the
    company: billing checks the count and makes it at its price, so neither the price nor whose
    wallet it pays into can be changed in the browser."""
    await require_editor(user, company_id)

    return TopUpCheckoutOut(
        transaction_id=await billing.company_checkout(company_id, body.candidates, user.uid)
    )
