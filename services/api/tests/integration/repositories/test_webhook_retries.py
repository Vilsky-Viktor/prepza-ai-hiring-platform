import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta

from api.constants.api import RETRY_LEASE
from api.handlers.dispatch import handle
from api.repositories import webhook_retries as retries
from api.repositories import webhooks
from tests.integration.transactions import transaction

# A company's most web hooks (MAX_WEBHOOKS in the limit list).
MAX_WEBHOOKS = 5


def test_an_event_is_kept_once_and_claimed_by_one_run_at_a_time(run):
    company = uuid.uuid4()
    past = datetime.now(UTC) - timedelta(seconds=1)

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )
        later = await transaction(
            webhooks.add, company, "https://example.com/y", "sealed", "u1", MAX_WEBHOOKS
        )
        # Twice: a redelivered event keeps the retry it has.
        await transaction(retries.add, hook.id, "e1", '{"id":"e1"}', past)
        await transaction(retries.add, hook.id, "e1", '{"id":"other"}', past)
        await transaction(
            retries.add, later.id, "e1", '{"id":"e1"}', datetime.now(UTC) + timedelta(hours=1)
        )
        # Two runs at once: each kept event goes to one of them.
        first, second = await asyncio.gather(
            transaction(retries.claim, 25), transaction(retries.claim, 25)
        )

        return hook, first + second, await transaction(retries.claim, 25)

    hook, claimed, again = run(scenario())
    ((row, found),) = claimed

    assert found.id == hook.id and found.url == "https://example.com/x"
    assert row.event_id == "e1" and row.body == '{"id":"e1"}' and row.attempts == 1
    # Put off while it's being sent, so a run cut off midway leaves it for a later one.
    assert row.next_at > datetime.now(UTC) + RETRY_LEASE - timedelta(minutes=1)
    assert again == []


def test_a_kept_event_waits_longer_goes_once_sent_and_with_its_web_hook(run):
    company = uuid.uuid4()
    past = datetime.now(UTC) - timedelta(seconds=1)

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )
        await transaction(retries.add, hook.id, "e1", "{}", past)
        await transaction(retries.add, hook.id, "e2", "{}", past)
        await transaction(retries.add, hook.id, "e3", "{}", past)
        await transaction(retries.postpone, hook.id, "e1", 2, past)
        await transaction(retries.remove, hook.id, "e2")
        claimed = await transaction(retries.claim, 25)
        await transaction(retries.add, hook.id, "e4", "{}", past)
        await transaction(webhooks.remove, company, hook.id, "u1")

        return claimed, await transaction(retries.claim, 25)

    claimed, after = run(scenario())

    assert sorted((row.event_id, row.attempts) for row, _ in claimed) == [("e1", 2), ("e3", 1)]
    assert after == []


def test_a_paused_web_hook_drops_its_waiting_retries_until_started_again(run):
    company = uuid.uuid4()
    past = datetime.now(UTC) - timedelta(seconds=1)

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )
        other = await transaction(
            webhooks.add, company, "https://example.com/y", "sealed", "u1", MAX_WEBHOOKS
        )
        await transaction(retries.add, hook.id, "e1", '{"id":"e1"}', past)
        await transaction(retries.add, other.id, "e1", '{"id":"e1"}', past)
        fresh = (await transaction(webhooks.of_company, company))[0].failing
        await transaction(webhooks.set_failing, hook.id, True)
        paused = {row.id: row.failing for row in await transaction(webhooks.of_company, company)}
        waiting = [row.webhook_id for row, _ in await transaction(retries.claim, 1000)]
        await transaction(webhooks.set_failing, hook.id, False)
        again = {row.id: row.failing for row in await transaction(webhooks.of_company, company)}

        return fresh, paused[hook.id], hook.id in waiting, other.id in waiting, again[hook.id]

    assert run(scenario()) == (False, True, False, True, False)


def test_an_erased_candidates_results_waiting_to_be_sent_again_go(run):
    """Only theirs: another candidate's, the same email in another interview and another
    company's stay."""
    company, other_company = uuid.uuid4(), uuid.uuid4()
    interview, other_interview = str(uuid.uuid4()), str(uuid.uuid4())
    past = datetime.now(UTC) - timedelta(seconds=1)

    def body(event_id, interview_id, email):
        data = {"interview": {"id": interview_id}, "candidate": {"email": email}}

        return json.dumps({"id": event_id, "type": "candidate.finished", "data": data})

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )
        theirs = await transaction(
            webhooks.add, other_company, "https://example.com/x", "sealed", "u2", MAX_WEBHOOKS
        )
        await transaction(
            retries.add, hook.id, "erased", body("erased", interview, "Ann@x.com"), past
        )
        await transaction(
            retries.add, hook.id, "other", body("other", interview, "bob@x.com"), past
        )
        await transaction(
            retries.add, hook.id, "elsewhere", body("elsewhere", other_interview, "ann@x.com"), past
        )
        await transaction(
            retries.add, theirs.id, "theirs", body("theirs", interview, "ann@x.com"), past
        )
        await handle(
            "candidate.removed",
            {"company_id": str(company), "interview_id": interview, "email": "ann@x.com"},
            "removed-1",
        )

        return sorted(row.event_id for row, _ in await transaction(retries.claim, 25))

    assert run(scenario()) == ["elsewhere", "other", "theirs"]


def test_a_deleted_account_or_interview_takes_its_waiting_results_with_it(run):
    company = uuid.uuid4()
    future = datetime.now(UTC) + timedelta(hours=1)
    interview, other = str(uuid.uuid4()), str(uuid.uuid4())

    def body(email, interview_id):
        data = {"candidate": {"email": email}, "interview": {"id": interview_id}}

        return json.dumps({"data": data})

    async def scenario():
        hook = await transaction(
            webhooks.add, company, "https://example.com/x", "sealed", "u1", MAX_WEBHOOKS
        )
        await transaction(retries.add, hook.id, "gone", body("Gone@Example.com", other), future)
        await transaction(
            retries.add, hook.id, "in-deleted", body("cy@example.com", interview), future
        )
        await transaction(retries.add, hook.id, "stays", body("bo@example.com", other), future)
        await transaction(retries.remove_email, "gone@example.com")
        # An unverified account's email is empty: it matches no one.
        await transaction(retries.remove_email, "")
        await handle(
            "candidate.interview_deleted",
            {"company_id": str(company), "interview_id": interview},
            "ev-1",
        )
        await transaction(
            retries.postpone, hook.id, "stays", 2, datetime.now(UTC) - timedelta(seconds=1)
        )

        return [row.event_id for row, _ in await transaction(retries.claim, 25)]

    assert run(scenario()) == ["stays"]
