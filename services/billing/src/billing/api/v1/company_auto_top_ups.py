"""A company's automatic top-up, for its members: owners and admins set it up, as they top up;
viewers only see it. Billing checks the member and their role itself through companies.
Reached at /api/companies/companies/{id}/auto-top-up, as before (the gateway sends it here)."""

from uuid import UUID

from fastapi import APIRouter, Request, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.http.visitor_country import VisitorCountry
from prepza_common.i18n.i18n import request_language

from billing.constants.products import OwnerType
from billing.integrations.companies import require
from billing.schemas.billing import AutoTopUpIn, AutoTopUpOut, CheckoutOut
from billing.services import auto_top_up_declines, auto_top_ups, checkout_calls
from billing.services import outbox as outbox_service
from billing.services.currencies import decide

router = APIRouter(prefix="/companies/{company_id}/auto-top-up", tags=["billing"])


@router.get("")
async def get_company_auto_top_up(
    company_id: UUID, user: CurrentUser, country: VisitorCountry = None
) -> AutoTopUpOut:
    """Priced in the currency it charges in: a running one's, or else the company's."""
    await require(company_id, user.uid)
    currency = await decide(country, company_id=str(company_id))

    return await auto_top_ups.out(OwnerType.COMPANY, str(company_id), currency)


@router.put("")
async def turn_on_company_auto_top_up(
    company_id: UUID,
    body: AutoTopUpIn,
    user: CurrentUser,
    request: Request,
    country: VisitorCountry = None,
) -> AutoTopUpOut:
    """Sets it up, or changes a running one the user's card pays for; what each charge buys is
    named on its invoice in the user's interface language. Turning it on makes the checkout's
    transaction in Paddle."""
    await require(company_id, user.uid, editor=True)
    await checkout_calls.count(user.uid, company_id)
    currency = await decide(country, company_id=str(company_id))
    saved = await auto_top_ups.turn_on(
        OwnerType.COMPANY,
        str(company_id),
        body,
        user.uid,
        currency,
        request_language(request),
        logged=True,
    )
    await outbox_service.flush_quietly()

    return saved


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def turn_off_company_auto_top_up(company_id: UUID, user: CurrentUser) -> None:
    await require(company_id, user.uid, editor=True)
    await auto_top_ups.turn_off(OwnerType.COMPANY, str(company_id), actor=user.uid)
    await outbox_service.flush_quietly()


@router.post("/card")
async def update_company_auto_top_up_card(company_id: UUID, user: CurrentUser) -> CheckoutOut:
    """The checkout that saves a new card for the automatic top-up, for the person whose card
    pays for it; a paused one starts again once the card is saved."""
    await require(company_id, user.uid, editor=True)
    await checkout_calls.count(user.uid, company_id)

    return await auto_top_up_declines.card_update(OwnerType.COMPANY, str(company_id), user.uid)
