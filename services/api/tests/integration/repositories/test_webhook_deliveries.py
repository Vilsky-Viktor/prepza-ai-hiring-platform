import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from api.core.db import Session
from api.repositories import webhooks
from tests.integration.transactions import transaction


def test_the_web_hooks_that_got_an_event_are_found_at_once(run):
    async def scenario():
        company = uuid.uuid4()
        first = await transaction(webhooks.add, company, "https://a.example/x", "sealed", "u1", 10)
        second = await transaction(webhooks.add, company, "https://b.example/x", "sealed", "u1", 10)
        await transaction(webhooks.mark_delivered, first.id, "e1")
        got = await transaction(webhooks.delivered_to, [first.id, second.id], "e1")
        await transaction(webhooks.remove_company, company)

        return got == {first.id}

    assert run(scenario())


def test_a_web_hooks_rows_carry_its_company(run):
    from api.models.api import WebhookAttempt, WebhookDelivery, WebhookRetry
    from api.repositories import webhook_log, webhook_retries

    async def scenario():
        company = uuid.uuid4()
        hook = await transaction(webhooks.add, company, "https://a.example/x", "sealed", "u1", 10)
        await transaction(webhooks.mark_delivered, hook.id, "e1")
        await transaction(webhook_retries.add, hook.id, "e2", "{}", datetime.now(UTC))
        await transaction(webhook_log.add, hook.id, "e1", "test", True, "delivered")

        async with Session() as session:
            found = [
                await session.scalar(select(model.company_id).where(model.webhook_id == hook.id))
                for model in (WebhookDelivery, WebhookRetry, WebhookAttempt)
            ]

        await transaction(webhooks.remove_company, company)

        return company, found

    company, found = run(scenario())

    assert found == [company, company, company]
