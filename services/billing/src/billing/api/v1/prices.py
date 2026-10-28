from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.user import Language
from prepza_common.config.constants import DEFAULT_LANGUAGE

from billing.api.dependencies import Country, ServiceCaller
from billing.config import settings
from billing.constants.currencies import ChoiceOwner, Currency
from billing.constants.products import CANDIDATES_OUT_OF_RANGE, TOP_UP_UNAVAILABLE, OwnerType
from billing.helpers.credits import custom_top_up
from billing.integrations import paddle
from billing.repositories import auto_top_ups, currencies
from billing.schemas.billing import (
    CatalogOut,
    CompanyCurrencyOut,
    CurrencyIn,
    TopUpCheckoutIn,
    TopUpCheckoutOut,
)
from billing.services.auto_top_up_prices import charge_price
from billing.services.catalog import candidates_price, catalog_out
from billing.services.currencies import decide, saved

# A company's prices and currency, and its top-up's checkout; companies checks the caller's role.
# `country` is the visitor's, which companies passes on.
router = APIRouter(prefix="/internal", tags=["internal"])


def company_currency(currency: Currency) -> CompanyCurrencyOut:
    return CompanyCurrencyOut(currency=currency)


@router.get("/companies/{company_id}/catalog")
async def company_catalog(
    company_id: str, caller: ServiceCaller, country: Country = None
) -> CatalogOut:
    """Every price in the currency the company pays in, wherever the buyer is."""
    return catalog_out(await decide(country, company_id=company_id))


@router.get("/companies/{company_id}/currency")
async def get_company_currency(
    company_id: str, caller: ServiceCaller, country: Country = None
) -> CompanyCurrencyOut:
    return company_currency(await decide(country, company_id=company_id))


@router.put("/companies/{company_id}/currency")
async def choose_company_currency(
    company_id: str, body: CurrencyIn, caller: ServiceCaller
) -> CompanyCurrencyOut:
    """From now on its top-ups are priced and charged in it, automatic ones too, at once and at
    the price list's price in it (their next charge switches the subscription over), which the
    answer says for a running one."""
    await currencies.choose(ChoiceOwner.COMPANY, company_id, body.currency)
    row = await auto_top_ups.get(OwnerType.COMPANY, company_id)
    chosen = company_currency(body.currency)

    if row is not None and row.subscription_id is not None:
        chosen.auto_top_up_price = charge_price(row, body.currency, datetime.now(UTC))

    return chosen


@router.post("/users/{user_id}/currency", status_code=status.HTTP_204_NO_CONTENT)
async def remember_user_currency(
    user_id: str, caller: ServiceCaller, country: Country = None
) -> None:
    """On sign-up: the new account sees prices in its country's currency, until changed."""
    await saved(ChoiceOwner.USER, user_id, country)


@router.post("/companies/{company_id}/checkout")
async def company_checkout(
    company_id: str,
    body: TopUpCheckoutIn,
    buyer_id: str,
    caller: ServiceCaller,
    country: Country = None,
    language: Language = DEFAULT_LANGUAGE,
) -> TopUpCheckoutOut:
    """A checkout for a top-up of `candidates`, paid into the company by `buyer_id`: companies
    has checked they're its owner or an admin. What it buys and its price are set here from the
    count, in the company's currency, which Paddle then charges wherever the buyer is; its item
    is named in the buyer's interface `language`. A count outside the range, or before Paddle's
    product is set, is refused (422)."""
    currency = await decide(country, company_id=company_id)
    bought = custom_top_up(body.candidates, currency)

    if bought is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, CANDIDATES_OUT_OF_RANGE)

    if not settings.paddle_product_candidates:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, TOP_UP_UNAVAILABLE)

    candidates, cents = bought
    custom = {"owner_type": OwnerType.COMPANY, "owner_id": company_id, "buyer_id": buyer_id}
    item = {"price": candidates_price(candidates, cents, currency, None, language), "quantity": 1}

    return TopUpCheckoutOut(
        transaction_id=await paddle.create_transaction([item], currency, custom)
    )
