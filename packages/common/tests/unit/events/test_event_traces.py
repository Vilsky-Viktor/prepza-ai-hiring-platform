"""An event carries the trace of the request that saved it, through the outbox and Pub/Sub, so
its consumer's log lines (and the calls and events it leads to) join that request's."""

import asyncio
import contextvars
import json
import logging
from datetime import UTC, datetime
from types import SimpleNamespace

from event_pushes import push
from testee_common.config.constants import TRACE_FIELD
from testee_common.events import outbox, pubsub
from testee_common.events.pubsub import PushBody, event_of
from testee_common.observability.logging import JsonFormatter, current_trace, trace_header

HEADER = "4bf92f3577b34da6a3ce929d0e0e4736/1;o=1"


def in_request(header, work):
    """Runs `work` in a fresh context, as a request bringing `header` would."""

    def run():
        trace_header.set(header)

        return work()

    return contextvars.Context().run(run)


def saved(header) -> list:
    rows = []
    session = SimpleNamespace(add=rows.append)
    in_request(header, lambda: outbox.add(session, SimpleNamespace, "a.done", {}))

    return rows


def test_an_event_keeps_the_trace_of_the_request_that_saved_it():
    assert saved(HEADER)[0].trace == HEADER
    assert saved(None)[0].trace is None


def test_the_trace_goes_with_the_event_as_an_attribute(monkeypatch):
    sent = []

    async def publish_batch(messages, timeout):
        sent.extend(messages)

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)
    rows = [
        SimpleNamespace(
            id=name,
            event_type="a.done",
            data={},
            attempts=0,
            published_at=None,
            created_at=datetime(2026, 10, 29, tzinfo=UTC),
            trace=trace,
        )
        for name, trace in (("traced", HEADER), ("untraced", None))
    ]

    # The scheduled flush runs in a request of its own: its trace never replaces the rows'.
    in_request("scheduler/2;o=1", lambda: asyncio.run(outbox.send(rows, 5)))

    assert sent[0]["attributes"][pubsub.TRACE_ATTRIBUTE] == HEADER
    assert pubsub.TRACE_ATTRIBUTE not in sent[1]["attributes"]


def test_an_event_published_without_an_outbox_carries_the_requests_trace(monkeypatch):
    sent = []

    async def publish_batch(messages, timeout):
        sent.extend(messages)

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)

    in_request(HEADER, lambda: asyncio.run(pubsub.publish("ai.used", {})))

    assert sent[0]["attributes"][pubsub.TRACE_ATTRIBUTE] == HEADER


def test_a_consumers_lines_and_calls_carry_the_events_trace(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "testee-prod")
    body = PushBody.model_validate(push("a.done", {}, trace=HEADER))

    def handle():
        event_of(body)
        record = logging.LogRecord("handler", logging.INFO, __file__, 1, "handled", None, None)

        return json.loads(JsonFormatter().format(record)), trace_header.get()

    line, passed_on = in_request("push/9;o=1", handle)

    assert line[TRACE_FIELD] == "projects/testee-prod/traces/4bf92f3577b34da6a3ce929d0e0e4736"
    assert passed_on == HEADER


def test_an_event_without_a_trace_leaves_the_pushs_own():
    body = PushBody.model_validate(push("a.done", {}))

    def handle():
        current_trace.set("projects/p/traces/push")
        event_of(body)

        return current_trace.get(), trace_header.get()

    assert in_request("push/9;o=1", handle) == ("projects/p/traces/push", "push/9;o=1")
