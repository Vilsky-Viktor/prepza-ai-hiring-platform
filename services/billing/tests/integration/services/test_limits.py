"""The limits superadmins edit, against the real database and Redis: kept, written to the hash
every service reads, healed after a Redis wipe, and every change kept."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from testee_common.auth.user import User
from testee_common.limits import limits
from testee_common.limits.limit_list import LIMITS, LIMITS_KEY
from testee_common.redis import memory_cache

from billing.api.v1 import schedules
from billing.models.usage import LimitHit
from billing.repositories import limit_hits, limit_settings, usage
from billing.services import limit_hit_lists, limit_values
from tests.integration.transactions import transaction

# One limit no other service's integration tests touch, as they share Redis database 15.
NAME = "REGISTRATIONS_PER_DAY"
DEFAULT = LIMITS[NAME].default
ANN = User(uid="ann", email="ann@example.com", email_verified=True, sign_in_provider="google.com")
BOB = User(uid="bob", email="bob@example.com", email_verified=True, sign_in_provider="google.com")


async def read(redis) -> int | float:
    """The value a service reads now, past its 30 seconds' cache."""
    memory_cache._entries.pop(LIMITS_KEY, None)

    return await limits.limit(redis(), NAME)


async def changes_of_mine() -> list[tuple]:
    return [
        (change.old_value, change.new_value, change.changed_by_email)
        for change in reversed(await transaction(limit_settings.changes, 1_000))
        if change.name == NAME
    ]


@pytest.fixture
def reset(run, redis):
    """The limit back at its default after each test."""
    yield

    run(limit_values.change(NAME, None, ANN))


def test_a_change_is_read_by_the_services_and_a_reset_brings_the_default_back(run, redis, reset):
    async def scenario():
        before = await changes_of_mine()
        await limit_values.change(NAME, 500, ANN)
        changed = await read(redis)
        await limit_values.change(NAME, None, BOB)

        return changed, await read(redis), (await changes_of_mine())[len(before) :]

    changed, back, history = run(scenario())

    assert (changed, back) == (500, DEFAULT)
    assert history == [(None, 500, "ann@example.com"), (500, None, "bob@example.com")]


def test_a_levels_seconds_changed_in_controls_start_the_next_new_test(run, redis):
    """The hard level's seconds a question, as the companies service reads them for a new test
    (the browser checks the Controls form that saves it, zn-level-seconds.spec.ts)."""
    hard = "QUESTION_SECONDS_HARD"

    async def scenario():
        await limit_values.change(hard, 80, ANN)
        memory_cache._entries.pop(LIMITS_KEY, None)
        changed = await limits.question_seconds(redis(), "hard")
        await limit_values.change(hard, None, ANN)
        memory_cache._entries.pop(LIMITS_KEY, None)

        return changed, await limits.question_seconds(redis(), "hard")

    assert run(scenario()) == (80, LIMITS[hard].default)


def test_a_value_out_of_bounds_changes_nothing(run, redis, reset):
    async def scenario():
        before = await changes_of_mine()

        with pytest.raises(HTTPException) as refused:
            await limit_values.change(NAME, LIMITS[NAME].highest + 1, ANN)

        return refused.value, await read(redis), (await changes_of_mine())[len(before) :]

    refused, value, history = run(scenario())

    assert (refused.status_code, refused.detail) == (422, "Use a value from 100 to 1000000.")
    assert (value, history) == (DEFAULT, [])


def test_a_redis_wipe_is_healed_by_the_next_sync(run, redis, reset):
    async def scenario():
        await limit_values.change(NAME, 700, ANN)
        await redis().delete(LIMITS_KEY)
        wiped = await read(redis)
        await schedules.sync_limits()

        return wiped, await read(redis)

    assert run(scenario()) == (DEFAULT, 700)


def test_a_sync_never_brings_back_a_reset_value(run, redis, reset):
    async def scenario():
        await limit_values.change(NAME, 700, ANN)
        await transaction(limit_settings.change, NAME, None, "ann", "ann@example.com")
        await schedules.sync_limits()

        return await read(redis)

    assert run(scenario()) == DEFAULT


def test_two_changes_at_once_each_keep_the_value_before_them(run, redis, reset):
    async def scenario():
        before = await changes_of_mine()
        await asyncio.gather(
            transaction(limit_settings.change, NAME, 300, "ann", "ann@example.com"),
            transaction(limit_settings.change, NAME, 400, "bob", "bob@example.com"),
        )

        return (await changes_of_mine())[len(before) :]

    first, second = run(scenario())

    # Locked: the second saw the first's value, not the default both started from.
    assert first[0] is None
    assert second[0] == first[1]


def test_a_limits_hits_of_the_last_7_days_and_who_hit_it_most(run, redis, reset, monkeypatch):
    acme, ann = str(uuid.uuid4()), f"ann-{uuid.uuid4().hex}"
    now = datetime.now(UTC)

    async def company_names(ids):
        return {acme: "Acme"}

    async def user_emails(ids):
        return {ann: "ann@example.com"}

    monkeypatch.setattr(limit_hit_lists, "company_names", company_names)
    monkeypatch.setattr(limit_hit_lists.names, "user_emails", user_emails)

    async def counted():
        found = await limit_values.limits_out()

        return next(item.hits for item in found.limits if item.name == NAME)

    async def scenario():
        before = await counted()
        hit = {"limit": NAME, "kind": "ours", "scope": "everyone"}

        for days in (1, 6, 8):
            who = {"company_id": acme, "user_id": ann}
            await transaction(
                usage.store_hit, uuid.uuid4().hex, now - timedelta(days=days), {**hit, **who}
            )

        lists = await limit_hit_lists.limit_hits_out(now.strftime("%Y-%m"))

        return await counted() - before, lists

    added, lists = run(scenario())
    shown = next(item for item in lists.ours if item.limit == NAME)

    assert added == 2
    assert shown.value == DEFAULT
    assert (shown.companies[0].id, shown.companies[0].name) == (acme, "Acme")
    assert (shown.users[0].id, shown.users[0].name) == (ann, "ann@example.com")


def test_only_each_limits_top_hitters_are_read(run):
    name = f"TEST_{uuid.uuid4().hex}"
    companies = [str(uuid.uuid4()) for _ in range(4)]
    now = datetime.now(UTC)

    async def scenario():
        for times, company in enumerate(companies, start=1):
            for _ in range(times):
                data = {"limit": name, "kind": "ours", "scope": "company", "company_id": company}
                await transaction(usage.store_hit, uuid.uuid4().hex, now, data)

        rows = await transaction(
            limit_hits.hitters, LimitHit.company_id, [LimitHit.limit == name], 2
        )

        return [(key, hits) for _, key, hits in rows]

    # The two that hit it most, most first; the rest aren't read.
    assert run(scenario()) == [(companies[3], 4), (companies[2], 3)]
