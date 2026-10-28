"""A member's web hook actions reach the company's action log through api's outbox, saved with
the change itself; the web hook is named by its site only. (API keys: test_key_permissions.)"""

import uuid
from datetime import UTC, datetime

from prepza_common.events.audit_actions import AUDIT_RECORDED
from sqlalchemy import select

from api.core.db import Session
from api.models.outbox import OutboxEvent
from api.repositories import webhooks
from tests.integration.transactions import transaction


async def logged(company) -> list[dict]:
    """The company's actions waiting in the outbox for its action log, oldest first."""
    query = (
        select(OutboxEvent.data)
        .where(
            OutboxEvent.event_type == AUDIT_RECORDED,
            OutboxEvent.data["company_id"].astext == str(company),
        )
        .order_by(OutboxEvent.created_at)
    )

    async with Session() as session:
        return list(await session.scalars(query))


def test_a_web_hook_added_tested_and_deleted_is_logged_by_its_site(run):
    company = uuid.uuid4()

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://hooks.zapier.com/secret/path", "s", "ann", 5
        )
        await transaction(webhooks.tested, hook, "bob")
        await transaction(webhooks.remove, company, hook.id, "ann")
        # Gone already: nothing more.
        await transaction(webhooks.remove, company, hook.id, "ann")

        return hook, await logged(company)

    hook, events = run(scenario())

    assert [(row["action"], row["user_id"], row["target_label"]) for row in events] == [
        ("webhook_added", "ann", "https://hooks.zapier.com/…"),
        ("webhook_tested", "bob", "https://hooks.zapier.com/…"),
        ("webhook_deleted", "ann", "https://hooks.zapier.com/…"),
    ]
    assert {(row["target_kind"], row["target_id"]) for row in events} == {("webhook", str(hook.id))}


def test_a_rolled_secret_keeps_the_old_one_until_its_overlap_ends_and_is_logged(run):
    company = uuid.uuid4()
    until = datetime(2026, 10, 23, 9, tzinfo=UTC)

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://hooks.example.com/x", "sealed-1", "ann", 5
        )
        rolled = await transaction(webhooks.rotate, company, hook.id, "sealed-2", until, "bob")
        # Another company's id finds nothing to roll.
        other = await transaction(webhooks.rotate, uuid.uuid4(), hook.id, "sealed-3", until, "eve")
        found = await transaction(webhooks.get, company, hook.id)

        return rolled, other, found, await logged(company)

    rolled, other, found, events = run(scenario())

    assert (found.secret, found.previous_secret, found.previous_until) == (
        "sealed-2",
        "sealed-1",
        until,
    )
    assert rolled is not None and other is None
    assert [(row["action"], row["user_id"]) for row in events][-1] == (
        "webhook_secret_rotated",
        "bob",
    )
