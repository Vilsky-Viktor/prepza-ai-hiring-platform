from fastapi import APIRouter, status
from prepza_common.auth.user import Language
from prepza_common.config.constants import DEFAULT_LANGUAGE

from billing.api.dependencies import Country, ServiceCaller
from billing.constants.products import OwnerType
from billing.schemas.billing import AutoTopUpIn, AutoTopUpOut, CheckoutOut
from billing.services import auto_top_up_declines, auto_top_ups
from billing.services.currencies import decide

# A company's automatic top-up, for companies' calls. Members reach company_auto_top_ups.py, so
# only DELETE (a member removed, the company deleted) is still called; the others are kept one
# release for a companies still calling them (microservices.md, 3), then removed. Prices are in a
# running one's currency, or else the company's; `country` is the visitor's.
internal = APIRouter(prefix="/internal", tags=["internal"])


@internal.get("/companies/{company_id}/auto-top-up")
async def company_auto_top_up(
    company_id: str, caller: ServiceCaller, country: Country = None
) -> AutoTopUpOut:
    currency = await decide(country, company_id=company_id)

    return await auto_top_ups.out(OwnerType.COMPANY, company_id, currency)


@internal.put("/companies/{company_id}/auto-top-up")
async def turn_on_company(
    company_id: str,
    body: AutoTopUpIn,
    buyer_id: str,
    caller: ServiceCaller,
    country: Country = None,
    language: Language = DEFAULT_LANGUAGE,
) -> AutoTopUpOut:
    """`language` is the buyer's interface language, which names what each charge buys."""
    currency = await decide(country, company_id=company_id)

    return await auto_top_ups.turn_on(
        OwnerType.COMPANY, company_id, body, buyer_id, currency, language
    )


@internal.delete("/companies/{company_id}/auto-top-up", status_code=status.HTTP_204_NO_CONTENT)
async def turn_off_company(
    company_id: str, caller: ServiceCaller, buyer_id: str | None = None
) -> None:
    """With `buyer_id`, off only when that person's card pays for it."""
    await auto_top_ups.turn_off(OwnerType.COMPANY, company_id, buyer_id)


@internal.post("/companies/{company_id}/auto-top-up/card")
async def update_company_card(company_id: str, buyer_id: str, caller: ServiceCaller) -> CheckoutOut:
    """The checkout that saves a new card for a running automatic top-up, for the person whose
    card pays for it; a paused one resumes once Paddle has saved it."""
    return await auto_top_up_declines.card_update(OwnerType.COMPANY, company_id, buyer_id)
