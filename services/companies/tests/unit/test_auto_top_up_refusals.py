import asyncio
import uuid

import httpx
import pytest
from fastapi import HTTPException
from prepza_common import http

from app.integrations import billing_prices as billing


@pytest.mark.parametrize("code", [403, 422])
def test_billings_refusal_reaches_the_user_unchanged(monkeypatch, code):
    """A choice it doesn't offer, or a running top-up paid by someone else's card."""
    detail = "Only the person whose card pays for it can change it."
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(code, json={"detail": detail}))
    )
    monkeypatch.setattr(http, "get_client", lambda: client)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(billing.turn_on_auto_top_up(uuid.uuid4(), {}, "bob", None, "en"))

    assert (refused.value.status_code, refused.value.detail) == (code, detail)


def test_a_checkout_sends_the_count_and_billings_refusal_reaches_the_user(monkeypatch):
    detail = "Choose from 10 to 1,000 candidates."
    sent = []

    def answer(request):
        sent.append((request.content, request.url.params["language"]))

        return httpx.Response(422, json={"detail": detail})

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(billing.company_checkout(uuid.uuid4(), 1_001, "bob", None, "uk"))

    assert (refused.value.status_code, refused.value.detail) == (422, detail)
    # The buyer's language goes along: billing names the item in it.
    assert sent == [(b'{"candidates":1001}', "uk")]


def test_turning_on_sends_the_buyers_language(monkeypatch):
    """Billing keeps it, to name what each automatic charge buys."""
    sent = []

    def answer(request):
        sent.append(request.url.params["language"])

        return httpx.Response(200, json={})

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)

    asyncio.run(billing.turn_on_auto_top_up(uuid.uuid4(), {}, "bob", None, "ja"))

    assert sent == ["ja"]


@pytest.mark.parametrize(
    ("code", "detail"),
    [
        (403, "Only the person whose card pays for it can change it."),
        (409, "Automatic top-up isn't on"),
    ],
)
def test_a_card_updates_refusal_reaches_the_user_unchanged(monkeypatch, code, detail):
    """Someone else's card pays for it, or it isn't running."""
    asked = []

    def answer(request):
        asked.append((request.url.path, request.url.params["buyer_id"]))

        return httpx.Response(code, json={"detail": detail})

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)
    company = uuid.uuid4()

    with pytest.raises(HTTPException) as refused:
        asyncio.run(billing.update_auto_top_up_card(company, "bob"))

    assert (refused.value.status_code, refused.value.detail) == (code, detail)
    assert asked == [(f"/internal/companies/{company}/auto-top-up/card", "bob")]
