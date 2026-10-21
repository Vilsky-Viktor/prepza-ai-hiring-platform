from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import CurrentUser
from prepza_common.visitor_country import VisitorCountry

from app.integrations import billing_prices as billing
from app.routers.billing import count_checkout_call
from app.schemas.auto_top_ups import AutoTopUpIn, AutoTopUpOut, CheckoutOut
from app.services.access import require_company, require_editor
from app.storage import audit

# Owners and admins set it up, as they top up; viewers only see it.
router = APIRouter(prefix="/companies/{company_id}/auto-top-up", tags=["companies"])


@router.get("")
async def get_auto_top_up(
    company_id: UUID, user: CurrentUser, country: VisitorCountry = None
) -> AutoTopUpOut:
    """Priced in the currency it charges in: a running one's, or else the company's."""
    await require_company(user, company_id)

    return AutoTopUpOut(**await billing.auto_top_up(company_id, country))


@router.put("")
async def turn_on(
    company_id: UUID, body: AutoTopUpIn, user: CurrentUser, country: VisitorCountry = None
) -> AutoTopUpOut:
    await require_editor(user, company_id)
    # Turning it on makes the checkout's transaction in Paddle.
    await count_checkout_call(user.uid, company_id)
    was_on = (await billing.auto_top_up(company_id))["on"]
    saved = await billing.turn_on_auto_top_up(company_id, body.model_dump(), user.uid, country)
    action = AuditAction.AUTO_TOP_UP_CHANGED if was_on else AuditAction.AUTO_TOP_UP_SET
    await audit.record(company_id, user.uid, action, company_id, target_kind=TargetKind.COMPANY)

    return AutoTopUpOut(**saved)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def turn_off(company_id: UUID, user: CurrentUser) -> None:
    await require_editor(user, company_id)
    await billing.turn_off_auto_top_up(company_id)
    await audit.record(
        company_id,
        user.uid,
        AuditAction.AUTO_TOP_UP_STOPPED,
        company_id,
        target_kind=TargetKind.COMPANY,
    )


@router.post("/card")
async def update_card(company_id: UUID, user: CurrentUser) -> CheckoutOut:
    """The checkout that saves a new card for the automatic top-up, for the person whose card
    pays for it; a paused one starts again once the card is saved."""
    await require_editor(user, company_id)
    await count_checkout_call(user.uid, company_id)

    return CheckoutOut(transaction_id=await billing.update_auto_top_up_card(company_id, user.uid))
