from fastapi import APIRouter, status
from prepza_common.auth.user import Language
from prepza_common.config.constants import DEFAULT_LANGUAGE

from billing.api.dependencies import Country, ServiceCaller
from billing.constants.currencies import ChoiceOwner, Currency
from billing.schemas.billing import (
    CatalogOut,
    CompanyCurrencyOut,
    CurrencyIn,
    TopUpCheckoutIn,
    TopUpCheckoutOut,
)
from billing.services import checkouts, currencies
from billing.services.catalog import catalog_out
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
    return await currencies.choose_company(company_id, body.currency)


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
    return await checkouts.company_checkout(
        company_id, body.candidates, buyer_id, country, language
    )
