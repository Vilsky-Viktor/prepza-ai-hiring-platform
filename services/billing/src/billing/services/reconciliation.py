import logging
from datetime import datetime

from billing.constants.reconciliation import RECONCILE_WINDOW
from billing.core.db import Session
from billing.integrations import paddle
from billing.repositories import purchases
from billing.services.adjustments import handle_adjustment
from billing.services.topups import handle_completed

logger = logging.getLogger(__name__)


async def reconcile(now: datetime) -> None:
    """Daily: does again, from Paddle's own records, what its web hooks of the last
    RECONCILE_WINDOW should have done, through the same idempotent handlers, so a web hook Paddle
    gave up on (a wrong secret, an outage) still adds the credits a payment bought and takes back
    those of a refund or chargeback. What it finds missing is logged; what was done is skipped.
    Transactions come first, so a refund whose payment's web hook was lost counts too."""
    since = now - RECONCILE_WINDOW
    transactions = await paddle.completed_transactions(since)
    ids = [transaction["id"] for transaction in transactions]
    known = await credited(ids)

    for transaction in transactions:
        if transaction["id"] not in known:
            await quietly(handle_completed, transaction)

    for found in await credited([id_ for id_ in ids if id_ not in known]):
        logger.warning("Reconciliation credited transaction %s: its web hook didn't", found)

    adjustments = await paddle.approved_adjustments(since)
    pairs = [(item["transaction_id"], item["id"]) for item in adjustments]
    done = await counted(pairs)

    for adjustment in adjustments:
        if adjustment["id"] not in done:
            await quietly(handle_adjustment, adjustment)

    for found in await counted(pairs) - done:
        logger.warning("Reconciliation counted adjustment %s: its web hook didn't", found)


async def credited(ids: list[str]) -> set[str]:
    async with Session() as session:
        return await purchases.credited(session, ids)


async def counted(pairs: list[tuple[str, str]]) -> set[str]:
    async with Session() as session:
        return await purchases.counted(session, pairs)


async def quietly(handler, data: dict) -> None:
    """One item's failure is logged and leaves the rest to go on; the next run tries it again."""
    try:
        await handler(data)
    except Exception:
        logger.exception("Reconciling %s failed", data.get("id"))
