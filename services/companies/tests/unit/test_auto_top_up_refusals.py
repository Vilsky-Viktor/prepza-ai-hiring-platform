import asyncio
import uuid

import httpx
import pytest
from fastapi import HTTPException
from prepza_common import http

from app.integrations import billing


@pytest.mark.parametrize("code", [403, 422])
def test_billings_refusal_reaches_the_user_unchanged(monkeypatch, code):
    """A choice it doesn't offer, or a running top-up paid by someone else's card."""
    detail = "Only the person whose card pays for it can change it."
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(code, json={"detail": detail}))
    )
    monkeypatch.setattr(http, "get_client", lambda: client)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(billing.turn_on_auto_top_up(uuid.uuid4(), {}, "bob"))

    assert (refused.value.status_code, refused.value.detail) == (code, detail)


def test_a_checkout_sends_the_count_and_billings_refusal_reaches_the_user(monkeypatch):
    detail = "Choose from 10 to 1,000 candidates."
    sent = []

    def answer(request):
        sent.append(request.content)

        return httpx.Response(422, json={"detail": detail})

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)

    with pytest.raises(HTTPException) as refused:
        asyncio.run(billing.company_checkout(uuid.uuid4(), 1_001, "bob"))

    assert (refused.value.status_code, refused.value.detail) == (422, detail)
    assert sent == [b'{"candidates":1001}']
