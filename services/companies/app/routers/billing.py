from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import CurrentUser
from prepza_common.i18n import request_language
from prepza_common.paging import PageParams
from prepza_common.rate_limit import hit_or_skip
from prepza_common.visitor_country import VisitorCountry

from app.integrations import billing, billing_prices
from app.integrations.redis import get_redis
from app.schemas.billing import (
    CreditCandidateOut,
    HistoryEntryOut,
    InvoiceOut,
    PaymentFailureOut,
    TopUpCheckoutIn,
    TopUpCheckoutOut,
)
from app.schemas.currencies import CatalogOut, CompanyCurrencyOut, CurrencyIn
from app.services import credit_history
from app.services.access import require_company, require_editor
from app.storage import audit

# Owners and admins, who top up, see where the credits went; viewers don't.
router = APIRouter(prefix="/companies/{company_id}/billing", tags=["companies"])


async def count_checkout_call(user_id: str, company_id: UUID) -> None:
    """One call to Paddle's API on the user's behalf; past the hourly limit, a 429. Against abuse,
    so Redis being down lets it through."""
    await hit_or_skip(
        get_redis(),
        f"rate:checkout-calls:{user_id}",
        "CHECKOUT_CALLS_PER_USER_HOUR",
        company_id=company_id,
        user_id=user_id,
    )


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
    await count_checkout_call(user.uid, company_id)

    return InvoiceOut(url=await billing.company_invoice(company_id, transaction_id))


@router.post("/checkout")
async def create_checkout(
    company_id: UUID,
    body: TopUpCheckoutIn,
    user: CurrentUser,
    request: Request,
    country: VisitorCountry = None,
) -> TopUpCheckoutOut:
    """A Paddle checkout for a top-up of some number of candidates, paid by the user into the
    company: billing checks the count and makes it at its price, in the company's currency, so
    neither the price, the currency nor whose wallet it pays into can be changed in the
    browser. Its item is named in the user's interface language."""
    await require_editor(user, company_id)
    await count_checkout_call(user.uid, company_id)

    return TopUpCheckoutOut(
        transaction_id=await billing_prices.company_checkout(
            company_id, body.candidates, user.uid, country, language=request_language(request)
        )
    )


@router.get("/catalog")
async def get_catalog(
    company_id: UUID, user: CurrentUser, country: VisitorCountry = None
) -> CatalogOut:
    """Every price in the currency the company pays in, for its top-up."""
    await require_editor(user, company_id)

    return CatalogOut(**await billing_prices.catalog(company_id, country))


@router.get("/currency")
async def get_currency(
    company_id: UUID,
    user: CurrentUser,
    country: VisitorCountry = None,
    page_country: Annotated[str | None, Query(alias="country")] = None,
) -> CompanyCurrencyOut:
    # `?country=` is the visitor's as a page's server passes it on, and wins over the header:
    # the server's own calls through the load balancer carry the server's country.
    await require_company(user, company_id)

    return CompanyCurrencyOut(**await billing_prices.currency(company_id, page_country or country))


@router.put("/currency")
async def choose_currency(
    company_id: UUID, body: CurrencyIn, user: CurrentUser
) -> CompanyCurrencyOut:
    """What the company's top-ups are priced and charged in from now on, automatic ones too."""
    await require_editor(user, company_id)
    chosen = await billing_prices.choose_currency(company_id, body.currency)
    await audit.record(
        company_id,
        user.uid,
        AuditAction.CURRENCY_CHANGED,
        company_id,
        target_kind=TargetKind.COMPANY,
    )

    return CompanyCurrencyOut(**chosen)


@router.get("/payment-failure")
async def get_payment_failure(
    company_id: UUID, transaction_id: str, user: CurrentUser
) -> PaymentFailureOut:
    """Why the latest payment of the user's own checkout into the company failed (a top-up's, or
    the one that saves the card for automatic top-up), for the site to say what to try next;
    404 for any other transaction."""
    await require_editor(user, company_id)
    await count_checkout_call(user.uid, company_id)

    return PaymentFailureOut(
        reason=await billing.company_payment_failure(company_id, transaction_id, user.uid)
    )
