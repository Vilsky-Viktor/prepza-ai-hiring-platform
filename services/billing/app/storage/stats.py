"""The admin zone's stats from billing's records. Purchases stay when an account or company is
deleted, so every top-up counts; a deleted company's spent credits go with its history."""

from prepza_common.stats import counted
from sqlalchemy import func, select

from app.constants.credits import Reason
from app.constants.currencies import Currency
from app.models.billing import Entry, Purchase
from app.storage.db import Session


async def stats(period: str | None) -> tuple[dict[str, int], dict[str, int]]:
    """All time or in `period` (a year or a month): the paid top-ups and the credits companies
    spent on candidates; and what the top-ups paid in each currency (minor units, tax included,
    refunds not taken off). Each product line of a transaction holds the whole transaction's
    total, so it counts once."""
    transactions = (
        select(
            func.min(Purchase.created_at).label("created_at"),
            func.min(Purchase.currency).label("currency"),
            func.max(Purchase.total_minor).label("paid"),
        )
        .group_by(Purchase.transaction_id)
        .subquery()
    )
    at = transactions.c.created_at

    async with Session() as session:
        paid = {
            currency: await counted(
                session,
                func.sum(transactions.c.paid),
                at,
                period,
                transactions.c.currency == currency,
            )
            for currency in Currency
        }
        counts = {
            "top_ups": await counted(session, func.count(at), at, period),
            "credits_spent": await counted(
                session,
                -func.sum(Entry.amount),
                Entry.created_at,
                period,
                Entry.reason == Reason.CANDIDATE,
            ),
        }

    return counts, paid
