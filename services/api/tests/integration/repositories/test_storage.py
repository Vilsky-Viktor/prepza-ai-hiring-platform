import os
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from event_pushes import push
from prepza_common.db.lock_waits import hold_first_commit, race
from sqlalchemy import select, update

from api.constants.api import DELIVERIES_KEPT, LAST_USED_EVERY
from api.core.db import Session
from api.main import app
from api.models.api import ApiKey, WebhookDelivery
from api.repositories import keys, webhooks
from tests.integration import transactions
from tests.integration.transactions import transaction

# A company's most keys and web hooks (MAX_API_KEYS and MAX_WEBHOOKS in the limit list).
MAX_KEYS = 10
MAX_WEBHOOKS = 5
# A new key's permissions.
READS = ["interviews:read", "candidates:read"]


def api() -> httpx.AsyncClient:
    """The app itself, called in the test's own event loop."""
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    return httpx.AsyncClient(transport=transport, base_url="http://api")


def test_a_key_is_found_by_its_hash_and_its_use_noted_at_most_once_a_minute(run):
    company = uuid.uuid4()
    hashed = uuid.uuid4().hex * 2

    async def scenario():
        made = await transaction(
            keys.add, company, "Site", "pz_abc", hashed, "u1", None, READS, [], MAX_KEYS
        )
        found = await transaction(keys.by_hash, hashed)
        await transaction(keys.used, made.id)
        first = (await transaction(keys.by_hash, hashed)).last_used_at
        await transaction(keys.used, made.id)
        again = (await transaction(keys.by_hash, hashed)).last_used_at

        # A minute on, it's noted again.
        async with Session() as session:
            earlier = first - LAST_USED_EVERY - timedelta(seconds=1)
            await session.execute(
                update(ApiKey).where(ApiKey.id == made.id).values(last_used_at=earlier)
            )
            await session.commit()

        await transaction(keys.used, made.id)
        later = (await transaction(keys.by_hash, hashed)).last_used_at

        return made, found, first, again, later

    made, found, first, again, later = run(scenario())

    assert found.id == made.id
    assert first is not None and again == first
    assert later > first - LAST_USED_EVERY


def test_a_web_hook_remembers_an_event_once_and_forgets_old_ones(run):
    company = uuid.uuid4()

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )
        await transaction(webhooks.mark_delivered, hook.id, "old")

        async with Session() as session:
            await session.execute(
                update(WebhookDelivery)
                .where(WebhookDelivery.event_id == "old")
                .values(delivered_at=datetime.now(UTC) - DELIVERIES_KEPT - timedelta(days=1))
            )
            await session.commit()

        # Twice: Pub/Sub may redeliver while the first is still being handled.
        await transaction(webhooks.mark_delivered, hook.id, "e1")
        await transaction(webhooks.mark_delivered, hook.id, "e1")

        return await transaction(webhooks.delivered, hook.id, "e1"), await transaction(
            webhooks.delivered, hook.id, "old"
        )

    new, old = run(scenario())

    assert new is True and old is False


def test_a_deleted_company_loses_its_keys_web_hooks_and_their_deliveries(run):
    company, other = uuid.uuid4(), uuid.uuid4()
    deleted = push("company.deleted", {"company_id": str(company)}, f"e-{uuid.uuid4()}")

    async def scenario():
        await transaction(
            keys.add, company, "Site", "pz_a", uuid.uuid4().hex * 2, "u1", None, READS, [], MAX_KEYS
        )
        await transaction(
            keys.add, other, "Site", "pz_b", uuid.uuid4().hex * 2, "u1", None, READS, [], MAX_KEYS
        )
        hook = await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )
        await transaction(webhooks.mark_delivered, hook.id, "e1")

        async with api() as client:
            codes = [
                (await client.post("/internal/events", json=deleted)).status_code for _ in range(2)
            ]

        async with Session() as session:
            deliveries = list(
                await session.scalars(
                    select(WebhookDelivery).where(WebhookDelivery.webhook_id == hook.id)
                )
            )

        return (
            codes,
            await transaction(keys.of_company, company),
            await transaction(keys.of_company, other),
            await transaction(webhooks.of_company, company),
            deliveries,
        )

    codes, left, others, hooks, deliveries = run(scenario())

    assert codes == [204, 204]
    assert left == [] and hooks == [] and deliveries == []
    assert len(others) == 1


def test_a_deleted_account_loses_the_keys_and_web_hooks_it_made(run):
    company = uuid.uuid4()

    async def scenario():
        await transaction(
            keys.add,
            company,
            "Mine",
            "pz_m",
            uuid.uuid4().hex * 2,
            "gone",
            None,
            READS,
            [],
            MAX_KEYS,
        )
        await transaction(
            keys.add,
            company,
            "Theirs",
            "pz_t",
            uuid.uuid4().hex * 2,
            "stays",
            None,
            READS,
            [],
            MAX_KEYS,
        )
        await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "gone", MAX_WEBHOOKS
        )
        exported = [key.name for key in await transaction(keys.of_user, "gone")]
        await transaction(keys.remove_user, "gone")
        await transaction(webhooks.remove_user, "gone")

        return (
            exported,
            [key.name for key in await transaction(keys.of_company, company)],
            await transaction(webhooks.of_user, "gone"),
        )

    exported, left, hooks = run(scenario())

    assert exported == ["Mine"]
    assert left == ["Theirs"]
    assert hooks == []


def test_one_below_the_limit_a_second_add_at_the_same_time_is_refused(run, monkeypatch):
    """The second add waits on the company's lock the first holds until it commits, then sees
    the limit reached."""
    company = uuid.uuid4()

    def new_key():
        return transaction(
            keys.add, company, "Site", "pz_x", uuid.uuid4().hex * 2, "u1", None, READS, [], MAX_KEYS
        )

    def new_hook():
        return transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )

    async def at_the_same_time(add):
        # The first add's transaction waits at its commit, holding the company's lock.
        held = hold_first_commit(monkeypatch, transactions)
        _, second = await race(os.environ["DATABASE_URL"], held, add(), add())

        return second

    async def scenario():
        for _ in range(MAX_KEYS - 1):
            await new_key()

        for _ in range(MAX_WEBHOOKS - 1):
            await new_hook()

        return (
            await at_the_same_time(new_key),
            await at_the_same_time(new_hook),
            len(await transaction(keys.of_company, company)),
            len(await transaction(webhooks.of_company, company)),
        )

    assert run(scenario()) == (None, None, MAX_KEYS, MAX_WEBHOOKS)
