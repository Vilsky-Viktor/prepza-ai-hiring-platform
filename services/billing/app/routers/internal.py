from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from prepza_common.analytics import track
from prepza_common.constants import MAX_PAGE_SIZE
from prepza_common.paging import PageParams

from app.constants.credits import (
    ADJUSTMENT_BELOW_ZERO,
    ADJUSTMENT_ZERO,
    CANDIDATE_CREDITS,
    CANDIDATE_PREFIX,
    NOT_ENOUGH,
    Reason,
)
from app.constants.currencies import ChoiceOwner
from app.constants.products import (
    MAX_BUYER_PURCHASES,
    OwnerType,
)
from app.helpers.history import history_entry_out
from app.helpers.wallets import balance_out, candidates_for
from app.integrations import paddle
from app.schemas.billing import (
    AdjustmentIn,
    BalanceOut,
    BuyerPurchaseOut,
    HistoryEntryOut,
    HoldOut,
    InvoiceOut,
    LowCompaniesOut,
    LowCompanyOut,
    OwnersIn,
    PaidOut,
    PurchaseOwnerOut,
    ReferralOut,
    WelcomeIn,
)
from app.service_auth import ServiceCaller
from app.services import auto_top_ups
from app.services.currencies import saved
from app.services.referrals import referral_out
from app.storage import auto_top_ups as auto_top_up_rows
from app.storage import currencies, history, ledger, purchases, referrals, usage

router = APIRouter(prefix="/internal", tags=["internal"])


async def refuse(owner_type: str, owner_id: str, reason: str) -> None:
    await track("balance_too_low", company_id=owner_id, what=reason)
    # An automatic top-up refills it for the next try.
    await auto_top_ups.check_briefly(owner_type, owner_id)

    raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, NOT_ENOUGH)


@router.post("/candidates/hold", status_code=status.HTTP_204_NO_CONTENT)
async def hold_candidate(company_id: str, key: str, caller: ServiceCaller) -> None:
    """Set aside on invite. Charged once the interview finishes with at least one answer. An
    automatic top-up the balance now calls for is charged before answering, waited for only
    briefly: Paddle can take its time, and the invite waiting on this answer mustn't."""
    held = await ledger.reserve(
        OwnerType.COMPANY, company_id, CANDIDATE_CREDITS, CANDIDATE_PREFIX + key, Reason.CANDIDATE
    )

    if not held:
        await refuse(OwnerType.COMPANY, company_id, Reason.CANDIDATE)

    await auto_top_ups.check_briefly(OwnerType.COMPANY, company_id)


@router.post("/candidates/charge", status_code=status.HTTP_204_NO_CONTENT)
async def charge_candidate(key: str, caller: ServiceCaller) -> None:
    await ledger.charge(CANDIDATE_PREFIX + key)


@router.post("/candidates/release", status_code=status.HTTP_204_NO_CONTENT)
async def release_candidate(key: str, caller: ServiceCaller) -> None:
    await ledger.release(CANDIDATE_PREFIX + key)


@router.get("/candidates/hold")
async def candidate_hold(key: str, caller: ServiceCaller) -> HoldOut:
    """Whether a candidate's credits are set aside, charged or given back, for the admin zone's
    support tab; 404 when none were held."""
    found = await ledger.hold_status(CANDIDATE_PREFIX + key)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return HoldOut(status=found)


@router.post("/companies/{company_id}/welcome", status_code=status.HTTP_204_NO_CONTENT)
async def welcome_company(company_id: str, body: WelcomeIn, caller: ServiceCaller) -> None:
    """The company's wallet. The welcome credits come once per owner's email; a company new
    in that sense can be referred by another, unrelated one."""
    if await ledger.welcome_company(company_id, body.owner_email) and body.referral:
        await referrals.record(body.referral, OwnerType.COMPANY, company_id, body.related)

    # It pays in the currency of the country it's created in, until changed.
    await saved(ChoiceOwner.COMPANY, company_id, body.country)


@router.get("/companies/{company_id}/paid")
async def company_paid(company_id: str, caller: ServiceCaller) -> PaidOut:
    return PaidOut(paid=await purchases.paid(OwnerType.COMPANY, company_id))


@router.get("/companies/{company_id}/referral")
async def company_referral(company_id: str, caller: ServiceCaller) -> ReferralOut:
    return await referral_out(OwnerType.COMPANY, company_id)


@router.get("/companies/{company_id}/credits")
async def company_credits(company_id: str, caller: ServiceCaller) -> BalanceOut:
    return balance_out(await ledger.wallet(OwnerType.COMPANY, company_id))


@router.get("/companies/{company_id}/history")
async def company_history(
    company_id: str, page: PageParams, caller: ServiceCaller
) -> list[HistoryEntryOut]:
    """Every movement of the company's credits, newest first."""
    rows = await history.page(OwnerType.COMPANY, company_id, page.offset, page.limit)

    return [history_entry_out(row) for row in rows]


@router.post("/companies/{company_id}/adjustments", status_code=status.HTTP_204_NO_CONTENT)
async def adjust_company(company_id: str, body: AdjustmentIn, caller: ServiceCaller) -> None:
    """A superadmin adds or removes credits (companies checks who and logs it). Safe to repeat
    with the same key; refused when it would take the available balance below zero."""
    if body.amount == 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ADJUSTMENT_ZERO)

    note = body.note.strip()
    key = f"adjustment:{body.key}"

    if not await ledger.adjust(OwnerType.COMPANY, company_id, body.amount, key, note):
        raise HTTPException(status.HTTP_409_CONFLICT, ADJUSTMENT_BELOW_ZERO)


@router.get("/companies/{company_id}/invoice")
async def company_invoice(
    company_id: str, transaction_id: str, caller: ServiceCaller
) -> InvoiceOut:
    """The invoice of one of the company's top-ups; 404 for anyone else's transaction."""
    if not await purchases.owns(OwnerType.COMPANY, company_id, transaction_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return InvoiceOut(url=await paddle.invoice_url(transaction_id))


@router.get("/purchases")
async def buyer_purchases(buyer_id: str, caller: ServiceCaller) -> list[BuyerPurchaseOut]:
    """The company top-ups someone paid for, one per transaction, newest first, at most
    MAX_BUYER_PURCHASES, for the admin zone's support tab."""
    return [
        BuyerPurchaseOut(
            transaction_id=row.transaction_id,
            company_id=row.owner_id,
            total=str(row.total),
            currency=row.currency,
            created_at=row.created_at,
        )
        for row in await purchases.bought_by(buyer_id, MAX_BUYER_PURCHASES)
    ]


@router.get("/purchases/{transaction_id}")
async def purchase_owner(transaction_id: str, caller: ServiceCaller) -> PurchaseOwnerOut:
    """Whose wallet a top-up's Paddle transaction paid into, for the admin zone's support
    search; 404 when no top-up has that transaction."""
    bought = await purchases.for_transaction(transaction_id)

    if bought is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    owner_type, owner_id, _, _ = bought

    return PurchaseOwnerOut(owner_type=owner_type, owner_id=owner_id)


@router.post("/companies/credits")
async def companies_credits(body: OwnersIn, caller: ServiceCaller) -> dict[str, BalanceOut]:
    """Several companies' balances at once, for the top-up page."""
    found = await ledger.wallets(OwnerType.COMPANY, body.owner_ids)
    empty = BalanceOut(balance=0, reserved=0, available=0, low=True, candidates=0)

    return {
        owner_id: balance_out(found[owner_id]) if owner_id in found else empty
        for owner_id in body.owner_ids
    }


@router.get("/companies/low")
async def low_companies(
    caller: ServiceCaller, ids: Annotated[list[str] | None, Query(max_length=MAX_PAGE_SIZE)] = None
) -> LowCompaniesOut:
    """Companies running low on credits that no automatic top-up refills: for notifications'
    reminders, and (only `ids`) the assistant's get_updates."""
    rows = await ledger.running_low(OwnerType.COMPANY, ids)

    return LowCompaniesOut(
        companies=[
            LowCompanyOut(
                company_id=row.owner_id,
                available=row.balance - row.reserved,
                candidates=candidates_for(row.balance - row.reserved),
            )
            for row in rows
        ]
    )


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: str, caller: ServiceCaller) -> None:
    await auto_top_ups.turn_off(OwnerType.COMPANY, company_id)
    await purchases.delete_company(company_id)
    await currencies.forget(ChoiceOwner.COMPANY, company_id)
    # Its AI costs and limit hits stay, without the company.
    await usage.forget("company_id", company_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, caller: ServiceCaller) -> None:
    """The user's purchases for their companies stay for bookkeeping, without their id, and so
    do their AI costs and limit hits; any automatic top-up paid with their card goes off."""
    await auto_top_ups.forget_buyer(user_id)
    await purchases.forget_buyer(user_id)
    await currencies.forget(ChoiceOwner.USER, user_id)
    await usage.forget("user_id", user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    """What the user bought for their companies, the automatic top-ups they turned on (charged
    to their card once started), and the currency they see prices in."""
    return jsonable_encoder(
        {
            "currency": await currencies.chosen(ChoiceOwner.USER, user_id),
            "auto_top_ups": [
                {
                    "company_id": row.owner_id,
                    "product": row.product,
                    "threshold": row.threshold,
                    "started": row.subscription_id is not None,
                    "last_charged_at": row.charged_at,
                    "last_declined_at": row.failed_at,
                }
                for row in await auto_top_up_rows.of_buyer(user_id)
            ],
            "purchases": [
                {
                    "product": item.product,
                    "quantity": item.quantity,
                    "total": str(item.total_minor),
                    "currency": item.currency,
                    "at": item.created_at,
                }
                for item in await purchases.purchases_of(user_id)
            ],
        }
    )
