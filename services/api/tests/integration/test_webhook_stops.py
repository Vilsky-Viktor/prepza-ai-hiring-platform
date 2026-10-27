import asyncio
import uuid
from datetime import UTC, datetime

from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import select

from app.models.outbox import OutboxEvent
from app.storage import webhooks
from app.storage.db import Session


def test_a_web_hook_stops_once_however_many_events_find_it_and_starts_again(run):
    notice = {"kind": "webhook_stopped", "recipient_id": str(uuid.uuid4())}

    async def scenario():
        company = uuid.uuid4()
        hook = await webhooks.add(company, "https://a.example/x", "sealed", "u1", 10)
        stopped = await asyncio.gather(
            *[webhooks.set_stopped(hook.id, True, notice) for _ in range(2)]
        )
        again = await webhooks.set_stopped(hook.id, True, notice)
        started = await webhooks.set_stopped(hook.id, False)

        async with Session() as session:
            told = list(
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.event_type == NOTIFICATION_REQUESTED,
                        OutboxEvent.data["recipient_id"].astext == notice["recipient_id"],
                    )
                )
            )

        await webhooks.remove_company(company)

        return sorted(stopped), again, started, told

    # The company is told once, with the change, through the outbox.
    assert run(scenario()) == ([False, True], False, True, [notice])


def test_the_web_hooks_that_got_an_event_are_found_at_once(run):
    async def scenario():
        company = uuid.uuid4()
        first = await webhooks.add(company, "https://a.example/x", "sealed", "u1", 10)
        second = await webhooks.add(company, "https://b.example/x", "sealed", "u1", 10)
        await webhooks.mark_delivered(first.id, "e1")
        got = await webhooks.delivered_to([first.id, second.id], "e1")
        await webhooks.remove_company(company)

        return got == {first.id}

    assert run(scenario())


def test_a_web_hooks_rows_carry_its_company(run):
    from app.models.api import WebhookAttempt, WebhookDelivery, WebhookRetry
    from app.storage import webhook_log, webhook_retries

    async def scenario():
        company = uuid.uuid4()
        hook = await webhooks.add(company, "https://a.example/x", "sealed", "u1", 10)
        await webhooks.mark_delivered(hook.id, "e1")
        await webhook_retries.add(hook.id, "e2", "{}", datetime.now(UTC))
        await webhook_log.add(hook.id, "e1", "test", True, "delivered")

        async with Session() as session:
            found = [
                await session.scalar(select(model.company_id).where(model.webhook_id == hook.id))
                for model in (WebhookDelivery, WebhookRetry, WebhookAttempt)
            ]

        await webhooks.remove_company(company)

        return company, found

    company, found = run(scenario())

    assert found == [company, company, company]
