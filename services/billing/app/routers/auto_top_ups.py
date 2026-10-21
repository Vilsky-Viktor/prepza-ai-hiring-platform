from fastapi import APIRouter, status

from app.constants.products import OwnerType
from app.dependencies import Country
from app.schemas.billing import AutoTopUpIn, AutoTopUpOut
from app.service_auth import ServiceCaller
from app.services import auto_top_ups
from app.services.currencies import decide

# A company's automatic top-up; companies checks that the user is one of its members. Prices
# are in a running one's currency, or else the company's; `country` is the visitor's, which
# companies passes on.
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
) -> AutoTopUpOut:
    currency = await decide(country, company_id=company_id)

    return await auto_top_ups.turn_on(OwnerType.COMPANY, company_id, body, buyer_id, currency)


@internal.delete("/companies/{company_id}/auto-top-up", status_code=status.HTTP_204_NO_CONTENT)
async def turn_off_company(
    company_id: str, caller: ServiceCaller, buyer_id: str | None = None
) -> None:
    """With `buyer_id`, off only when that person's card pays for it."""
    await auto_top_ups.turn_off(OwnerType.COMPANY, company_id, buyer_id)
