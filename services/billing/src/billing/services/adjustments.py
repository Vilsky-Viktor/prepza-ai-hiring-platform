import logging

from prepza_common.events.analytics import track

from billing.constants.credits import Reason
from billing.constants.products import ADJUSTMENT_APPROVED
from billing.core.db import Session
from billing.repositories import ledger, purchases
from billing.services import credit_events
from billing.services.referrals import take_back_reward

logger = logging.getLogger(__name__)

# Paddle's adjustment action, and whether it takes the credits back (-1) or returns them (+1).
ACTIONS = {
    "refund": (Reason.REFUND, -1),
    "chargeback": (Reason.CHARGEBACK, -1),
    "chargeback_reverse": (Reason.CHARGEBACK_REVERSED, 1),
}


def share(granted: int, adjusted_total: str, paid: int) -> int:
    """The part of the credits a payment bought that an adjustment of `adjusted_total` covers;
    a full refund is all of them."""
    if paid <= 0:
        return 0

    return granted * min(int(adjusted_total), paid) // paid


async def handle_adjustment(data: dict) -> None:
    """Takes back the credits of an approved refund or a chargeback, and returns them when a
    chargeback is reversed. Each adjustment counts once, however often Paddle sends it. The
    balance may go negative if the credits were spent; then nothing can be spent until a
    top-up covers it. Taking back all of a top-up also takes back the referral rewards it paid
    (not returned by a chargeback's reversal: the company's next top-up pays them again)."""
    found = ACTIONS.get(data.get("action"))

    if found is None or data.get("status") != ADJUSTMENT_APPROVED:
        return

    reason, sign = found

    async with Session() as session:
        bought = await purchases.for_transaction(session, data["transaction_id"])
        existing = bought and await ledger.wallets(session, bought[0], [bought[1]])

    if bought is None:
        logger.warning("Adjustment %s is for a transaction we didn't sell", data["id"])

        return

    owner_type, owner_id, granted, paid = bought

    # Its company was deleted, credits and all: nothing to take back but the referral reward
    # the top-up paid, when it's all refunded, so deleting a referred company can't keep it.
    if owner_id not in existing:
        if sign < 0 and int(data["totals"]["total"]) >= paid:
            await take_back_reward(owner_id, data["transaction_id"])

        return

    credits = share(granted, data["totals"]["total"], paid)

    if not credits:
        return

    # Several partial refunds of the whole top-up count as a full one.
    # A chargeback reversed gives the credits back: other services hear of it.
    async with Session.begin() as session:
        taken = await purchases.take_back(
            session,
            owner_type,
            owner_id,
            sign * credits,
            data["transaction_id"],
            data["id"],
            reason,
            data["totals"]["total"],
            data.get("currency_code"),
            [credit_events.credits_added(owner_type, owner_id)] if sign > 0 else [],
        )

    await track(
        "credits_taken_back",
        company_id=owner_id,
        why=reason,
        credits=sign * credits,
    )

    if sign < 0 and granted and taken >= granted:
        await take_back_reward(owner_id, data["transaction_id"])
