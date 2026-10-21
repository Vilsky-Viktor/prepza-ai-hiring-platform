"""Calls to Paddle's API: Paddle failing is logged for its alert; a refusal isn't."""

import asyncio
import logging

import httpx
import pytest
from prepza_common import http

from app.constants.products import PADDLE_API_VERSION
from app.integrations import paddle


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
