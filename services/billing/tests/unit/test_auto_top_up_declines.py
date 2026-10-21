"""An automatic charge Paddle refuses: a declined card is the owner's to fix and they're told;
Paddle refusing billing itself (its key, a permission, its rate limit) is never told to them as
their card's."""

import asyncio

import httpx
import pytest

from app.services import auto_top_ups
from app.storage import auto_top_ups as rows


def refused(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://sandbox-api.paddle.com/subscriptions/sub_1/charge")

    return httpx.HTTPStatusError(
        "refused", request=request, response=httpx.Response(status, request=request)
    )


@pytest.fixture
def charging(monkeypatch):
    """A running automatic top-up whose charge Paddle answers with the status given."""
    told = []

    async def claim_charge(owner_type, owner_id, now):
        return object()

    async def failed(owner_type, owner_id, now):
        told.append("failed")

    async def publish_quietly(message):
        told.append("notified")

    def charge_answering(status):
        async def charge(row, owner_id):
            raise refused(status)

        monkeypatch.setattr(auto_top_ups, "charge", charge)

    monkeypatch.setattr(rows, "claim_charge", claim_charge)
    monkeypatch.setattr(rows, "failed", failed)
    monkeypatch.setattr(auto_top_ups, "publish_quietly", publish_quietly)

    return charge_answering, told


@pytest.mark.parametrize("status", [400, 402, 422])
def test_a_declined_card_waits_and_the_owner_is_told(charging, status):
    charge_answering, told = charging
    charge_answering(status)

    asyncio.run(auto_top_ups.check("company", "acme"))

    assert told == ["failed", "notified"]


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_paddle_refusing_billing_isnt_the_owners_card(charging, status):
    charge_answering, told = charging
    charge_answering(status)

    asyncio.run(auto_top_ups.check("company", "acme"))

    assert told == []
