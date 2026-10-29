from fastapi import APIRouter, status

from billing.api.dependencies import ServiceCaller
from billing.constants.products import OwnerType
from billing.services import auto_top_ups

# A company's automatic top-up goes off, for companies' calls (a member removed or made a viewer,
# the company deleted). Members reach company_auto_top_ups.py.
internal = APIRouter(prefix="/internal", tags=["internal"])


@internal.delete("/companies/{company_id}/auto-top-up", status_code=status.HTTP_204_NO_CONTENT)
async def turn_off_company(
    company_id: str, caller: ServiceCaller, buyer_id: str | None = None
) -> None:
    """With `buyer_id`, off only when that person's card pays for it."""
    await auto_top_ups.turn_off(OwnerType.COMPANY, company_id, buyer_id)
