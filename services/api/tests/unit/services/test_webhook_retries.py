import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from api.constants.api import (
    RETRY_BATCH,
    RETRY_FIRST_DELAY,
    RETRY_GIVE_UP,
    RETRY_MAX_DELAY,
)
from api.helpers import webhooks as webhook_helpers
from api.helpers.webhooks import retry_delay
from api.services import webhooks as delivery
from tests.unit.services.test_webhook_delivery import finish


def due(endpoints, hook, event_id="e1", age=timedelta(minutes=5)):
    """The kept event's time came; it was first kept `age` ago."""
    row = endpoints["retries"][(hook.id, event_id)]
    row.next_at = datetime.now(UTC) - timedelta(seconds=1)
    row.created_at = datetime.now(UTC) - age

    return row


def run():
    return asyncio.run(delivery.retry())


def failed_once(endpoints, url="https://down.example/x"):
    hook = endpoints["hook"](url)
    endpoints["failing"].add(url)
    finish()

    return hook


def test_the_wait_doubles_up_to_a_limit():
    assert retry_delay(1, 0) == RETRY_FIRST_DELAY
    assert retry_delay(2, 0) == RETRY_FIRST_DELAY * 2
    assert retry_delay(3, 0) == RETRY_FIRST_DELAY * 4
    assert retry_delay(30, 0) == RETRY_MAX_DELAY


@pytest.mark.parametrize(
    ("attempts", "share", "wait"),
    [
        (3, 1, RETRY_FIRST_DELAY * 2),
        (3, 0.5, RETRY_FIRST_DELAY * 3),
        (30, 1, RETRY_MAX_DELAY / 2),
        # Never sooner than the first wait.
        (1, 1, RETRY_FIRST_DELAY),
    ],
)
def test_the_wait_is_spread_by_up_to_half(attempts, share, wait):
    """Events that failed together come back at different times."""
    assert retry_delay(attempts, share) == wait


def test_waits_differ_between_events_that_failed_together():
    assert len({retry_delay(8) for _ in range(20)}) > 1


def test_an_event_isnt_sent_again_before_its_time(endpoints):
    failed_once(endpoints)
    endpoints["failing"].clear()

    assert run() == 0
    assert endpoints["posted"] == []


def test_an_event_sent_again_and_taken_is_done(endpoints):
    hook = failed_once(endpoints)
    endpoints["failing"].clear()
    due(endpoints, hook)

    assert run() == 1

    ((url, body, signature),) = endpoints["posted"]

    assert url == "https://down.example/x" and body["id"] == "e1"
    assert signature.startswith("t=")
    assert endpoints["retries"] == {}
    assert (hook.id, "e1") in endpoints["delivered"]

    # A redelivered event doesn't send it again.
    finish()

    assert len(endpoints["posted"]) == 1


def test_an_event_that_fails_again_waits_up_to_twice_as_long(endpoints, monkeypatch):
    # The random share of the wait taken off: a quarter of it (half of the most).
    monkeypatch.setattr(webhook_helpers.random, "random", lambda: 0.5)
    hook = failed_once(endpoints)
    due(endpoints, hook)
    run()
    row = endpoints["retries"][(hook.id, "e1")]
    wait = row.next_at - datetime.now(UTC)
    expected = RETRY_FIRST_DELAY * 2 * 0.75

    assert row.attempts == 2
    assert expected - timedelta(minutes=1) < wait <= expected
    assert hook.failing is False


def test_after_days_of_failing_the_web_hook_is_paused_until_a_test_event_goes_through(endpoints):
    hook = failed_once(endpoints)
    due(endpoints, hook, age=RETRY_GIVE_UP)
    run()

    assert endpoints["retries"] == {}
    assert hook.failing is True

    # Paused: the next event isn't sent, even once the endpoint answers again.
    endpoints["failing"].clear()
    sent = len(endpoints["posted"])
    finish("e2")

    assert len(endpoints["posted"]) == sent
    assert endpoints["retries"] == {}

    # A test event that goes through starts it again.
    assert asyncio.run(delivery.test(hook)) is True
    assert hook.failing is False

    finish("e3")

    assert endpoints["posted"][-1][1]["id"] == "e3"


def test_an_event_with_nowhere_to_go_any_more_is_dropped_unsent(endpoints, companies_api):
    left = failed_once(endpoints, "https://left.example/x")
    got = failed_once(endpoints, "https://got.example/x")
    endpoints["failing"].clear()
    left.created_by = "u2"
    companies_api["roles"]["u2"] = "viewer"
    endpoints["delivered"].add((got.id, "e1"))
    due(endpoints, left)
    due(endpoints, got)

    assert run() == 2
    assert endpoints["posted"] == []
    assert endpoints["retries"] == {}


def test_the_schedule_sends_kept_events_again(client, monkeypatch):
    runs = []

    async def retry():
        runs.append(True)

        return 1

    monkeypatch.setattr(delivery, "retry", retry)

    assert client.post("/internal/schedules/webhook-retries").status_code == 204
    assert runs == [True]


def test_the_retry_job_sends_batch_after_batch_until_none_are_due(endpoints, monkeypatch):
    batches = [RETRY_BATCH, RETRY_BATCH, 3]

    async def retry_batch():
        return batches.pop(0)

    monkeypatch.setattr(delivery, "retry_batch", retry_batch)

    assert run() == 2 * RETRY_BATCH + 3
    assert batches == []


def test_the_retry_job_starts_no_batch_once_its_time_is_up(endpoints, monkeypatch):
    clock = {"now": 0.0}

    async def retry_batch():
        # Each full batch takes 15 seconds.
        clock["now"] += 15

        return RETRY_BATCH

    monkeypatch.setattr(delivery.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(delivery, "retry_batch", retry_batch)

    # Started at 0, 15 and 30; not at 45, past RETRY_RUN_SECONDS.
    assert run() == 3 * RETRY_BATCH
