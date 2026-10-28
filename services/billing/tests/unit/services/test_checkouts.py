import asyncio

from billing.repositories import ledger
from billing.services import webhooks
from tests.unit.paddle_events import completed
from tests.unit.services.test_webhooks import granted  # noqa: F401 (fixture)


def test_a_checkout_opened_in_the_browser_grants_nothing(granted):  # noqa: F811
    event = completed()
    event["data"]["origin"] = "web"

    asyncio.run(webhooks.handle(event))

    assert granted == []


def test_a_payment_into_a_deleted_company_grants_nothing(granted, monkeypatch):  # noqa: F811
    async def none(owner_type, owner_ids):
        return {}

    monkeypatch.setattr(ledger, "wallets", none)

    asyncio.run(webhooks.handle(completed()))

    assert granted == []
