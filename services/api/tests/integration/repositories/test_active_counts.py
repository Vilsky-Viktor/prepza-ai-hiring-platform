"""What the company's menu counts: its keys that still work and its web hooks that get events."""

import uuid
from datetime import UTC, datetime, timedelta

from api.repositories import keys, webhooks
from tests.integration.transactions import transaction

READS = ["interviews:read"]


def test_only_the_companys_keys_that_still_work_are_counted(run):
    company, other, now = uuid.uuid4(), uuid.uuid4(), datetime.now(UTC)

    async def key(company_id, expires_at):
        hashed = uuid.uuid4().hex * 2
        await transaction(
            keys.add, company_id, "Site", "pz_a", hashed, "u1", expires_at, READS, [], 10
        )

    async def scenario():
        await key(company, None)
        await key(company, now + timedelta(days=1))
        await key(company, now - timedelta(seconds=1))
        await key(other, None)
        counted = await transaction(keys.live_count, company, now)

        for company_id in (company, other):
            await transaction(keys.remove_company, company_id)

        return counted

    # Never expiring and not yet expired; not the expired one, nor another company's.
    assert run(scenario()) == 2


def test_only_the_companys_web_hooks_that_get_events_are_counted(run):
    company, other = uuid.uuid4(), uuid.uuid4()

    async def hook(company_id):
        return await transaction(
            webhooks.add, company_id, "https://a.example/x", "sealed", "u1", 10
        )

    async def scenario():
        await hook(company)
        failing, stopped = await hook(company), await hook(company)
        await hook(other)
        await transaction(webhooks.set_failing, failing.id, True)
        await transaction(webhooks.set_stopped, stopped.id, True)
        counted = await transaction(webhooks.working_count, company)

        for company_id in (company, other):
            await transaction(webhooks.remove_company, company_id)

        return counted

    assert run(scenario()) == 1
