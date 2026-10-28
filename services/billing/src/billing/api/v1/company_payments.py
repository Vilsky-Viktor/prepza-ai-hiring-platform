"""A company's payments, for its members: its prices and currency, a top-up's checkout, an
invoice and why a payment failed. Billing checks the member and their role itself through
companies (integrations/companies.py); owners and admins pay, viewers only see the currency.
Reached at /api/companies/companies/{id}/billing/..., as before (the gateway sends these here)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.http.visitor_country import VisitorCountry
from prepza_common.i18n.i18n import request_language

from billing.constants.payment_failures import TRANSACTION_ID_PATTERN
from billing.constants.products import OwnerType
from billing.integrations.companies import require
from billing.schemas.billing import (
    CatalogOut,
    CompanyCurrencyOut,
    CurrencyIn,
    InvoiceOut,
    PaymentFailureOut,
    TopUpCheckoutIn,
    TopUpCheckoutOut,
)
from billing.services import checkout_calls, checkouts, currencies, invoices, payment_failures
from billing.services import outbox as outbox_service
from billing.services.catalog import catalog_out
from billing.services.currencies import decide

router = APIRouter(prefix="/companies/{company_id}/billing", tags=["billing"])


@router.get("/catalog")
async def get_company_catalog(
    company_id: UUID, user: CurrentUser, country: VisitorCountry = None
) -> CatalogOut:
    """Every price in the currency the company pays in, for its top-up."""
    await require(company_id, user.uid, editor=True)

    return catalog_out(await decide(country, company_id=str(company_id)))


@router.get("/currency")
async def get_company_currency(
    company_id: UUID,
    user: CurrentUser,
    country: VisitorCountry = None,
    page_country: Annotated[str | None, Query(alias="country")] = None,
) -> CompanyCurrencyOut:
    # `?country=` is the visitor's as a page's server passes it on, and wins over the header:
    # the server's own calls through the load balancer carry the server's country.
    await require(company_id, user.uid)

    return CompanyCurrencyOut(
        currency=await decide(page_country or country, company_id=str(company_id))
    )


@router.put("/currency")
async def choose_company_currency(
    company_id: UUID, body: CurrencyIn, user: CurrentUser
) -> CompanyCurrencyOut:
    """What the company's top-ups are priced and charged in from now on, automatic ones too."""
    await require(company_id, user.uid, editor=True)
    chosen = await currencies.choose_company(str(company_id), body.currency, user.uid)
    await outbox_service.flush_quietly()

    return chosen


@router.post("/checkout")
async def create_company_checkout(
    company_id: UUID,
    body: TopUpCheckoutIn,
    user: CurrentUser,
    request: Request,
    country: VisitorCountry = None,
) -> TopUpCheckoutOut:
    """A Paddle checkout for a top-up of some number of candidates, paid by the user into the
    company, at the count's price in the company's currency: neither the price, the currency nor
    whose wallet it pays into comes from the browser. Its item is named in the user's interface
    language."""
    await require(company_id, user.uid, editor=True)
    await checkout_calls.count(user.uid, company_id)

    return await checkouts.company_checkout(
        str(company_id), body.candidates, user.uid, country, request_language(request)
    )


@router.get("/invoice")
async def get_company_invoice(
    company_id: UUID, transaction_id: str, user: CurrentUser
) -> InvoiceOut:
    """A temporary link to the invoice of one of the company's top-ups."""
    await require(company_id, user.uid, editor=True)
    await checkout_calls.count(user.uid, company_id)

    return await invoices.company_invoice(str(company_id), transaction_id)


@router.get("/payment-failure")
async def get_company_payment_failure(
    company_id: UUID,
    transaction_id: Annotated[str, Query(pattern=TRANSACTION_ID_PATTERN)],
    user: CurrentUser,
) -> PaymentFailureOut:
    """Why the latest payment of the user's own checkout into the company failed (a top-up's, or
    the one that saves the card for automatic top-up), for the site to say what to try next;
    404 for any other transaction, so its id alone reveals nothing."""
    await require(company_id, user.uid, editor=True)
    await checkout_calls.count(user.uid, company_id)
    reason = await payment_failures.failure(
        OwnerType.COMPANY, str(company_id), user.uid, transaction_id
    )

    if reason is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return PaymentFailureOut(reason=reason)
