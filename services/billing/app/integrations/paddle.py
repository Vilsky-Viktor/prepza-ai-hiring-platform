import logging

import httpx
from prepza_common import http
from prepza_common.http import bearer

from app.config.settings import settings
from app.constants.products import PADDLE_API, PADDLE_API_VERSION

logger = logging.getLogger(__name__)


async def _call(method: str, path: str, **kwargs) -> httpx.Response:
    """One call to Paddle's API; a refusal raises. Paddle itself failing (no answer, or a 5xx) is
    logged as "Paddle unavailable", which the "prepza Paddle failing" alert counts; a refusal,
    such as a declined card, isn't."""
    try:
        response = await http.get_client().request(
            method,
            f"{PADDLE_API[settings.paddle_environment]}{path}",
            headers={**bearer(settings.paddle_api_key), "Paddle-Version": PADDLE_API_VERSION},
            **kwargs,
        )
    except httpx.TransportError as error:
        logger.error("Paddle unavailable: %s", type(error).__name__)

        raise

    if response.status_code >= 500:
        logger.error("Paddle unavailable: %d", response.status_code)

    response.raise_for_status()

    return response


async def charge(subscription_id: str, price: dict) -> None:
    """Bills one top-up, at a `price` made here in the subscription's currency, to its saved
    card now. Its transaction.completed webhook adds the credits; a declined card raises and
    changes nothing."""
    await _call(
        "POST",
        f"/subscriptions/{subscription_id}/charge",
        json={
            "effective_from": "immediately",
            "items": [{"price": price, "quantity": 1}],
            "on_payment_failure": "prevent_change",
        },
    )


async def set_currency(subscription_id: str, currency: str) -> None:
    """Switches the subscription (the $0 one that keeps the card) to bill in `currency`, billing
    nothing for the change."""
    await _call(
        "PATCH",
        f"/subscriptions/{subscription_id}",
        json={"currency_code": currency, "proration_billing_mode": "do_not_bill"},
    )


async def create_transaction(items: list[dict], currency: str, custom_data: dict) -> str:
    """A checkout's transaction, with whose wallet it's for set here, not in the browser, in
    `currency`, which Paddle then charges wherever the buyer is; Paddle.js opens it by its id."""
    response = await _call(
        "POST",
        "/transactions",
        json={"items": items, "currency_code": currency, "custom_data": custom_data},
    )

    return response.json()["data"]["id"]


async def cancel(subscription_id: str) -> None:
    """Ends the subscription at once, so the card isn't kept for us."""
    await _call(
        "POST",
        f"/subscriptions/{subscription_id}/cancel",
        json={"effective_from": "immediately"},
    )


async def subscription_status(subscription_id: str) -> str:
    """The subscription's status now: active, canceled and so on."""
    response = await _call("GET", f"/subscriptions/{subscription_id}")

    return response.json()["data"]["status"]


async def invoice_url(transaction_id: str) -> str:
    """A temporary link to the transaction's invoice PDF."""
    response = await _call("GET", f"/transactions/{transaction_id}/invoice")

    return response.json()["data"]["url"]


async def transaction(transaction_id: str, timeout: float) -> dict:
    """The transaction as Paddle has it now: its custom data and payment attempts."""
    response = await _call("GET", f"/transactions/{transaction_id}", timeout=timeout)

    return response.json()["data"]
