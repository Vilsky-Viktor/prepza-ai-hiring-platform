import logging
from datetime import UTC, datetime

import httpx
from prepza_common.http import http
from prepza_common.http.http import bearer

from app.config.settings import settings
from app.constants.products import PADDLE_API, PADDLE_API_VERSION, PADDLE_REFUSES_BILLING
from app.constants.reconciliation import PADDLE_PAGE_SIZE, RECONCILE_MAX_PAGES

logger = logging.getLogger(__name__)


async def _call(method: str, path: str, **kwargs) -> httpx.Response:
    """One call to Paddle's API; a refusal raises. Paddle failing (no answer, or a 5xx) or
    refusing billing itself (its key wrong, expired or short of a permission; rate-limited) is
    logged as "Paddle unavailable", which the "prepza Paddle failing" alert counts; a refusal of
    the request, such as a declined card, isn't."""
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

    if response.status_code >= 500 or response.status_code in PADDLE_REFUSES_BILLING:
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


async def charge_error(subscription_id: str, since: datetime, timeout: float) -> str | None:
    """Why the card declined the subscription's latest charge made since `since`: the last
    failed payment's error code, None when Paddle shows none."""
    params = {
        "subscription_id": subscription_id,
        "created_at[GTE]": since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "order_by": "created_at[DESC]",
        "per_page": 1,
    }
    response = await _call("GET", "/transactions", params=params, timeout=timeout)
    payments = [
        payment
        for transaction in response.json()["data"]
        for payment in transaction.get("payments", [])
        if payment.get("error_code")
    ]

    return payments[0]["error_code"] if payments else None


async def card_update_transaction(subscription_id: str) -> str:
    """The transaction whose checkout saves a new card for the subscription."""
    response = await _call(
        "GET", f"/subscriptions/{subscription_id}/update-payment-method-transaction"
    )

    return response.json()["data"]["id"]


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


async def completed_transactions(since: datetime) -> list[dict]:
    """Paddle's completed transactions updated since `since`, oldest first, as its web hooks
    send them; at most RECONCILE_MAX_PAGES pages."""
    params = {
        "status": "completed",
        "updated_at[GTE]": since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "order_by": "updated_at[ASC]",
        "per_page": PADDLE_PAGE_SIZE,
    }

    return await _pages("/transactions", params, lambda item: False)


async def approved_adjustments(since: datetime) -> list[dict]:
    """Paddle's approved adjustments (refunds, chargebacks and their reversals) created since
    `since`, newest first, as its web hooks send them; at most RECONCILE_MAX_PAGES pages."""
    params = {"status": "approved", "order_by": "id[DESC]", "per_page": PADDLE_PAGE_SIZE}

    def older(item: dict) -> bool:
        return datetime.fromisoformat(item["created_at"]) < since

    return await _pages("/adjustments", params, older)


async def _pages(path: str, params: dict, past_end) -> list[dict]:
    """A list's items, page after page, up to the first for which `past_end` is true."""
    found = []

    for _ in range(RECONCILE_MAX_PAGES):
        body = (await _call("GET", path, params=params)).json()

        for item in body["data"]:
            if past_end(item):
                return found

            found.append(item)

        if not body["data"] or not body["meta"]["pagination"]["has_more"]:
            return found

        params = {**params, "after": body["data"][-1]["id"]}

    logger.warning("Paddle's %s has over %d pages: the rest waits", path, RECONCILE_MAX_PAGES)

    return found
