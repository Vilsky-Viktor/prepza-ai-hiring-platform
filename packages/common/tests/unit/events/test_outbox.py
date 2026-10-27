import asyncio
import contextvars
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
from prepza_common.config.constants import OUTBOX_BATCH, OUTBOX_MAX_ATTEMPTS
from prepza_common.events import outbox, pubsub


def row(name, attempts=0):
    return SimpleNamespace(
        id=name,
        event_type=f"{name}.done",
        data={},
        attempts=attempts,
        published_at=None,
        created_at=datetime(2026, 10, 15, tzinfo=UTC),
    )


def status_error(code):
    request = httpx.Request("POST", "https://pubsub")

    return httpx.HTTPStatusError("refused", request=request, response=httpx.Response(code))


@pytest.fixture
def calls(monkeypatch):
    """Pub/Sub, faked: it rejects any call that carries a "bad" event."""
    sent = []

    async def publish_batch(messages, timeout):
        ids = [message["attributes"]["event_id"] for message in messages]
        sent.append(ids)

        if "bad" in ids:
            raise status_error(400)

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)

    return sent


def test_a_batch_is_published_in_one_call(calls):
    rows = [row("a"), row("b")]

    asyncio.run(outbox.send(rows, 5))

    assert calls == [["a", "b"]]
    assert all(item.published_at for item in rows)


def test_a_rejected_event_is_counted_alone_and_the_others_still_go(calls):
    good, bad, other = row("a"), row("bad"), row("c")

    asyncio.run(outbox.send([good, bad, other], 5))

    assert calls == [["a", "bad", "c"], ["a"], ["bad"], ["c"]]
    assert good.published_at and other.published_at
    assert bad.published_at is None and bad.attempts == 1


def test_an_event_rejected_too_often_is_parked(calls, caplog):
    bad = row("bad", attempts=OUTBOX_MAX_ATTEMPTS - 1)

    asyncio.run(outbox.send([bad], 5))

    assert bad.attempts == OUTBOX_MAX_ATTEMPTS
    # Logged as an error, which Sentry reports.
    [record] = [item for item in caplog.records if "parked" in item.message]
    assert record.levelname == "ERROR"


def test_an_outage_raises_and_counts_against_no_event(monkeypatch):
    async def down(messages, timeout):
        raise status_error(503)

    monkeypatch.setattr(pubsub, "publish_batch", down)
    rows = [row("a"), row("b")]

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(outbox.send(rows, 5))

    assert [item.attempts for item in rows] == [0, 0]


def test_a_quiet_flush_publishes_only_the_events_this_request_saved(monkeypatch):
    flushed = []

    async def flush(sessionmaker, model, ids, timeout):
        flushed.append((ids, timeout))

    monkeypatch.setattr(outbox, "flush", flush)
    session = SimpleNamespace(add=lambda item: None)

    async def request():
        outbox.add(session, SimpleNamespace, "a.done", {})
        outbox.add(session, SimpleNamespace, "b.done", {})
        await outbox.flush_quietly(None, None)
        # Nothing new saved: nothing to publish.
        await outbox.flush_quietly(None, None)

    async def other_request():
        await outbox.flush_quietly(None, None)

    contextvars.Context().run(asyncio.run, request())
    contextvars.Context().run(asyncio.run, other_request())

    [(ids, timeout)] = flushed
    assert len(ids) == 2
    assert timeout == 5


@pytest.fixture
def batches(monkeypatch):
    """The scheduled flush, with each batch's (published, taken) given in turn."""
    calls = []

    def run(*results):
        queue = list(results)

        async def flush_batch(sessionmaker, model, ids, timeout):
            calls.append(ids)

            return queue.pop(0)

        async def delete_old(sessionmaker, model):
            calls.append("delete")

        monkeypatch.setattr(outbox, "flush_batch", flush_batch)
        monkeypatch.setattr(outbox, "delete_old", delete_old)

        return asyncio.run(outbox.flush(None, None))

    run.calls = calls

    return run


def test_the_scheduled_flush_sends_batches_until_none_wait(batches):
    full = (OUTBOX_BATCH, OUTBOX_BATCH)

    assert batches(full, full, (30, 30)) == 2 * OUTBOX_BATCH + 30
    assert batches.calls == [None, None, None, "delete"]


def test_a_rejected_event_ends_the_run_and_waits_for_the_next(batches):
    assert (
        batches((OUTBOX_BATCH - 1, OUTBOX_BATCH), (OUTBOX_BATCH, OUTBOX_BATCH)) == OUTBOX_BATCH - 1
    )
    assert batches.calls == [None, "delete"]


def test_the_scheduled_flush_starts_no_batch_after_its_time(batches, monkeypatch):
    monkeypatch.setattr(outbox, "OUTBOX_FLUSH_SECONDS", 0)
    full = (OUTBOX_BATCH, OUTBOX_BATCH)

    assert batches(full, full) == OUTBOX_BATCH
    assert batches.calls == [None, "delete"]


def test_an_outage_ends_the_run_and_still_deletes_old_events(monkeypatch):
    deleted = []

    async def down(sessionmaker, model, ids, timeout):
        raise ConnectionError("Pub/Sub is down")

    async def delete_old(sessionmaker, model):
        deleted.append(True)

    monkeypatch.setattr(outbox, "flush_batch", down)
    monkeypatch.setattr(outbox, "delete_old", delete_old)

    with pytest.raises(ConnectionError):
        asyncio.run(outbox.flush(None, None))

    assert deleted == [True]


def test_an_event_that_stands_for_a_delivery_keeps_its_given_id():
    """Saved twice under one id (a provider's delivery), the row's key keeps one."""
    rows = []
    session = SimpleNamespace(add=rows.append)
    given = uuid.uuid4()

    async def request():
        outbox.add(session, SimpleNamespace, "email.webhook_received", {}, given)
        outbox.add(session, SimpleNamespace, "a.done", {})

    contextvars.Context().run(asyncio.run, request())

    assert rows[0].id == given and rows[1].id != given
