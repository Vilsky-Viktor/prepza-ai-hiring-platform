"""Calls to Paddle's API: Paddle failing is logged for its alert; a refusal isn't."""

import asyncio
import logging
from datetime import UTC, datetime

import httpx
import pytest
from prepza_common.http import http

from billing.constants.products import PADDLE_API_VERSION
from billing.integrations import paddle


def answering(status: int):
    def answer(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"data": {"status": "active"}})

    return answer


def unreachable(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("no route", request=request)


def use(monkeypatch, handler) -> None:
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )


@pytest.mark.parametrize(
    ("handler", "logged"),
    [
        (answering(503), "Paddle unavailable: 503"),
        (unreachable, "Paddle unavailable: ConnectError"),
        # The API key wrong or expired, short of a permission, or over Paddle's rate limit.
        (answering(401), "Paddle unavailable: 401"),
        (answering(403), "Paddle unavailable: 403"),
        (answering(429), "Paddle unavailable: 429"),
    ],
)
def test_paddle_failing_raises_and_is_logged_for_the_alert(monkeypatch, caplog, handler, logged):
    use(monkeypatch, handler)

    with caplog.at_level(logging.ERROR), pytest.raises(httpx.HTTPError):
        asyncio.run(paddle.subscription_status("sub_1"))

    assert logged in caplog.text


@pytest.mark.parametrize("status", [400, 402, 404, 422])
def test_a_refusal_such_as_a_declined_card_isnt_an_outage(monkeypatch, caplog, status):
    use(monkeypatch, answering(status))

    with caplog.at_level(logging.ERROR), pytest.raises(httpx.HTTPStatusError):
        asyncio.run(paddle.charge("sub_1", "pri_1"))

    assert "Paddle unavailable" not in caplog.text


def test_an_answer_is_read(monkeypatch):
    use(monkeypatch, answering(200))

    assert asyncio.run(paddle.subscription_status("sub_1")) == "active"


def test_every_call_asks_for_the_api_version_billing_reads(monkeypatch):
    seen = []

    def answer(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("Paddle-Version"))

        return httpx.Response(200, json={"data": {"status": "active", "url": "u", "id": "t"}})

    use(monkeypatch, answer)

    asyncio.run(paddle.subscription_status("sub_1"))
    asyncio.run(paddle.invoice_url("txn_1"))
    asyncio.run(paddle.create_transaction([], "USD", {}))

    assert seen == [PADDLE_API_VERSION] * 3


@pytest.mark.parametrize(
    ("transactions", "code"),
    [
        # Paddle lists a transaction's payments newest first: the latest failure's code.
        ([{"payments": [{"error_code": "fraud"}, {"error_code": "declined"}]}], "fraud"),
        ([{"payments": [{"error_code": None}]}], None),
        ([], None),
    ],
)
def test_why_a_subscriptions_charge_declined_is_read_from_its_latest_transaction(
    monkeypatch, transactions, code
):
    asked = []

    def answer(request: httpx.Request) -> httpx.Response:
        asked.append(request.url)

        return httpx.Response(200, json={"data": transactions})

    use(monkeypatch, answer)
    since = datetime(2026, 10, 21, 15, 30, tzinfo=UTC)

    assert asyncio.run(paddle.charge_error("sub_1", since, 2)) == code
    assert asked[0].path == "/transactions"
    assert dict(asked[0].params) == {
        "subscription_id": "sub_1",
        "created_at[GTE]": "2026-10-21T15:30:00Z",
        "order_by": "created_at[DESC]",
        "per_page": "1",
    }


def test_the_card_update_checkout_is_paddles_transaction_for_the_subscription(monkeypatch):
    asked = []

    def answer(request: httpx.Request) -> httpx.Response:
        asked.append((request.method, request.url.path))

        return httpx.Response(200, json={"data": {"id": "txn_card"}})

    use(monkeypatch, answer)

    assert asyncio.run(paddle.card_update_transaction("sub_1")) == "txn_card"
    assert asked == [("GET", "/subscriptions/sub_1/update-payment-method-transaction")]
