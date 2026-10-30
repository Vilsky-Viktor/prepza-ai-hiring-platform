"""A deleted company's or account's billing data, and an account's export."""

from billing.constants.currencies import ChoiceOwner
from billing.constants.products import OwnerType
from billing.core.db import Session
from billing.repositories import auto_top_ups as auto_top_up_rows
from billing.repositories import currencies, ledger, purchases, referrals, usage
from billing.services import auto_top_ups


async def delete_company(company_id: str) -> None:
    """Its automatic top-up off first (Paddle cancels its card's subscription, or this raises and
    the deletion is tried again); its holds and history a batch at a time; then its wallet,
    referral and currency in one save. Its purchases stay for the accounts, and its AI costs and
    limit hits without the company."""
    await auto_top_ups.turn_off(OwnerType.COMPANY, company_id)
    await ledger.delete_history(Session, company_id)

    async with Session.begin() as session:
        await ledger.delete_wallet(session, company_id)
        await referrals.forget(session, OwnerType.COMPANY, company_id)
        await currencies.forget(session, ChoiceOwner.COMPANY, company_id)

    await usage.forget(Session, "company_id", company_id)


async def delete_user(user_id: str) -> None:
    """The subscriptions of the automatic top-ups paid with the user's card are cancelled first
    (or this raises and the deletion is tried again); then, in one save, those top-ups go off,
    their purchases for their companies stay without them and their currency goes. One started
    meanwhile is cancelled after. Their AI costs and limit hits stay, without them."""
    cancelled = await auto_top_ups.cancel_for_buyer(user_id)

    async with Session.begin() as session:
        left = await auto_top_up_rows.remove_for_buyer(session, user_id)
        await purchases.forget_buyer(session, user_id)
        await currencies.forget(session, ChoiceOwner.USER, user_id)

    for subscription_id in set(left) - cancelled:
        await auto_top_ups.cancel(subscription_id)

    await usage.forget(Session, "user_id", user_id)


async def export(user_id: str) -> dict:
    """What the user bought for their companies, the automatic top-ups they turned on (charged
    to their card once started), the currency they see prices in, and the records of their AI
    use and of the limits that refused them (never the text sent to the AI)."""
    async with Session() as session:
        currency = await currencies.chosen(session, ChoiceOwner.USER, user_id)
        turned_on = await auto_top_up_rows.of_buyer(session, user_id)
        bought = await purchases.purchases_of(session, user_id)
        calls, hits = await usage.of_user(session, user_id)

    return {
        "currency": currency,
        "auto_top_ups": [
            {
                "company_id": row.owner_id,
                "product": row.product,
                "threshold": row.threshold,
                "started": row.subscription_id is not None,
                "agreed_at": row.agreed_at,
                "last_charged_at": row.charged_at,
                "last_declined_at": row.failed_at,
            }
            for row in turned_on
        ],
        "purchases": [
            {
                "product": item.product,
                "quantity": item.quantity,
                "total": str(item.total_minor),
                "currency": item.currency,
                "at": item.created_at,
            }
            for item in bought
        ],
        "ai_usage": [
            {
                "at": row.occurred_at,
                "action": row.action,
                "model": row.model,
                "company_id": row.company_id,
                "outcome": row.outcome,
            }
            for row in calls
        ],
        "limits_reached": [
            {
                "at": row.occurred_at,
                "limit": row.limit,
                "company_id": row.company_id,
                "what": row.what,
            }
            for row in hits
        ],
    }
