"""Charging an automatic top-up: after credits are used, the chosen top-up is bought with the
saved card once the balance is under its threshold."""

import asyncio
import logging
from datetime import UTC, datetime

from prepza_common.config.constants import DEFAULT_LANGUAGE

from billing.constants.currencies import DEFAULT_CURRENCY, Currency
from billing.constants.products import AUTO_TOP_UP_WAIT_SECONDS, TOP_UPS
from billing.core.db import Session
from billing.integrations import paddle
from billing.models.billing import AutoTopUp
from billing.repositories import auto_top_up_charges, auto_top_ups
from billing.services.auto_top_up_declines import declined, handle_decline
from billing.services.auto_top_up_prices import charge_price
from billing.services.catalog import candidates_price
from billing.services.currencies import decide

logger = logging.getLogger(__name__)


async def check_briefly(owner_type: str, owner_id: str) -> None:
    """check(), waited for at most AUTO_TOP_UP_WAIT_SECONDS, so the request that used the credits
    isn't held long and nothing runs after its answer. Cut off, the charge counts as one whose
    answer was lost: its web hook adds the credits if Paddle took it."""
    try:
        await asyncio.wait_for(check(owner_type, owner_id), AUTO_TOP_UP_WAIT_SECONDS)
    except TimeoutError:
        logger.warning("Automatic top-up cut off for %s %s", owner_type, owner_id)


def top_up_item(product_key: str, price: int, currency: Currency, language: str) -> dict:
    """The fixed top-up the automatic top-up buys, at `price` (minor units) in `currency`, named
    in `language`."""
    product = next(product for product in TOP_UPS if product.key == product_key)

    return candidates_price(
        product.candidates, price // product.candidates, currency, product.key, language
    )


async def charge(row: AutoTopUp, owner_id: str, now: datetime) -> tuple[int, Currency]:
    """Charges the chosen top-up in the company's currency now, at its agreed price
    (charge_price); what it charged. Paddle charges a subscription in its own currency
    (converting a price in another), so one set up in another currency is switched to the
    company's first, nothing billed for the switch."""
    currency = await decide(None, company_id=owner_id)
    price = charge_price(row, currency, now)

    if (row.currency or DEFAULT_CURRENCY) != currency:
        await paddle.set_currency(row.subscription_id, currency)

        async with Session.begin() as session:
            await auto_top_ups.set_currency(session, row.subscription_id, currency)

    # Named in the language of whoever turned it on; set up before languages were kept, English.
    item = top_up_item(row.product, price, currency, row.language or DEFAULT_LANGUAGE)
    await paddle.charge(row.subscription_id, item)

    return price, currency


async def check(owner_type: str, owner_id: str) -> None:
    """After credits are used: if the balance is now under the threshold, buys the chosen
    top-up with the saved card. Never fails the request that used the credits. A charge Paddle
    refuses (a declined card) is told to the company and tried again later, a few times at
    most (AUTO_TOP_UP_RETRY_WAITS), or never, once the decline can't pass later: then it pauses
    until the card is updated (auto_top_up_declines). After a timeout or Paddle's own error the
    charge may have gone through: its transaction.completed web hook adds the credits. Until a
    charge's credits come, none follows it, for at most AUTO_TOP_UP_UNCREDITED_WAIT
    (claim_charge). The claim is saved before Paddle is asked, and what it charged after."""
    row = None
    now = datetime.now(UTC)

    try:
        async with Session.begin() as session:
            row = await auto_top_ups.claim_charge(session, owner_type, owner_id, now)

        if row is None:
            return

        price, currency = await charge(row, owner_id, now)
    except Exception as error:
        logger.exception("Automatic top-up failed for %s %s", owner_type, owner_id)

        if row is not None and declined(error):
            await handle_decline(row, owner_type, owner_id, now)

        return

    async with Session.begin() as session:
        await auto_top_up_charges.charged(session, owner_type, owner_id, price, currency, now)
