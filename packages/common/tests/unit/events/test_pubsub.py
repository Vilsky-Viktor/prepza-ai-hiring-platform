import asyncio
import base64
import json
from datetime import UTC, datetime
from unittest import mock

import pytest
from testee_common.events import pubsub
from testee_common.events.pubsub import PushBody, event_of, publish
from testee_common.http import http


class FakeClient:
    def __init__(self):
        self.calls = []

    async def post(self, url, json, headers, timeout):
        self.calls.append((url, json, headers))

        return mock.Mock(raise_for_status=lambda: None)


@pytest.fixture
def client(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(http, "get_client", lambda: fake)

    return fake


def test_publishing_to_the_emulator_sends_the_event_without_a_token(client, monkeypatch):
    monkeypatch.setenv("PUBSUB_EMULATOR_HOST", "pubsub:8085")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-testee")

    asyncio.run(publish("candidate.invited", {"email": "bob@example.com"}))

    [(url, body, headers)] = client.calls
    [message] = body["messages"]
    assert url == "http://pubsub:8085/v1/projects/demo-testee/topics/events:publish"
    assert message["attributes"]["type"] == "candidate.invited"
    # Its family, which subscriptions filter on (infra/terraform/pubsub.tf).
    assert message["attributes"]["family"] == "candidate"
    assert json.loads(base64.b64decode(message["data"])) == {"email": "bob@example.com"}
    assert headers == {}


def test_publishing_to_google_carries_the_services_token(client, monkeypatch):
    monkeypatch.delenv("PUBSUB_EMULATOR_HOST", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "testee-prod")
    monkeypatch.setattr(pubsub, "access_token", lambda: "google-token")

    asyncio.run(publish("answer.recorded", {}))

    [(url, _, headers)] = client.calls
    assert url == "https://pubsub.googleapis.com/v1/projects/testee-prod/topics/events:publish"
    assert headers == {"Authorization": "Bearer google-token"}


def test_a_push_decodes_to_its_type_data_and_id():
    body = PushBody.model_validate(
        {
            "message": {
                "data": base64.b64encode(b'{"set_id": "s"}').decode(),
                "attributes": {"type": "generation.completed"},
                "messageId": "42",
            },
            "subscription": "projects/p/subscriptions/companies-events",
        }
    )

    assert event_of(body) == ("generation.completed", {"set_id": "s"}, "42")


def test_a_batch_goes_in_one_call_with_each_events_own_id(client, monkeypatch):
    monkeypatch.setenv("PUBSUB_EMULATOR_HOST", "pubsub:8085")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-testee")

    asyncio.run(
        pubsub.publish_batch(
            [
                pubsub.message("a.done", {}, "id-1", datetime(2026, 10, 15, tzinfo=UTC)),
                pubsub.message("b.done", {}),
            ]
        )
    )

    [(_, body, _)] = client.calls
    [given, new] = [message["attributes"] for message in body["messages"]]
    # With when it happened, the same on a re-send.
    assert given == {
        "type": "a.done",
        "family": "a",
        "event_id": "id-1",
        "occurred_at": "2026-10-15T00:00:00+00:00",
    }
    assert new["type"] == "b.done"
    assert new["event_id"]


def test_each_event_without_an_id_gets_its_own():
    """Never Pub/Sub's message id, which the local emulator numbers from 1 again after a restart:
    a new event must not look like one a consumer already handled."""
    first = pubsub.message("notification.requested", {})["attributes"]["event_id"]
    second = pubsub.message("notification.requested", {})["attributes"]["event_id"]

    assert first and second and first != second


def test_a_push_with_an_event_id_is_known_by_it_across_re_sends():
    body = PushBody.model_validate(
        {
            "message": {
                "attributes": {"type": "candidate.invited", "event_id": "row-1"},
                "messageId": "43",
            },
            "subscription": "projects/p/subscriptions/notifications-events",
        }
    )

    assert event_of(body) == ("candidate.invited", {}, "row-1")


def test_an_event_says_when_it_happened_else_when_it_was_published():
    def push(attributes, publish_time=None):
        message = pubsub.PushMessage(attributes=attributes, messageId="1", publishTime=publish_time)

        return pubsub.PushBody(message=message, subscription="s")

    happened = push({"occurred_at": "2026-10-15T08:00:00+00:00"}, "2026-10-15T09:00:00Z")
    older = push({}, "2026-10-15T09:00:00Z")

    assert pubsub.occurred_at(happened) == datetime(2026, 10, 15, 8, tzinfo=UTC)
    assert pubsub.occurred_at(older) == datetime(2026, 10, 15, 9, tzinfo=UTC)


def test_a_record_is_published_again_after_a_jittered_wait_and_given_up_quietly(monkeypatch):
    tries, slept = [], []

    async def down(messages, timeout):
        tries.append(messages[0]["attributes"]["event_id"])
        raise ConnectionError("down")

    async def sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(pubsub, "publish_batch", down)
    monkeypatch.setattr(pubsub.asyncio, "sleep", sleep)

    asyncio.run(pubsub.publish_retried("ai.used", {"a": 1}, 3, 1))

    # One id for every try, so a try that reached Pub/Sub after all is stored once.
    assert len(tries) == 3 and len(set(tries)) == 1
    assert len(slept) == 2 and all(0 <= wait <= 0.4 for wait in slept)


def test_a_record_waits_no_longer_than_its_time_in_all(monkeypatch):
    """A Pub/Sub that hangs costs the request recording it `timeout` seconds, not one per try."""
    tries = []

    async def hangs(messages, timeout):
        tries.append(timeout)
        await asyncio.Event().wait()

    monkeypatch.setattr(pubsub, "publish_batch", hangs)

    async def timed():
        started = asyncio.get_running_loop().time()
        await pubsub.publish_retried("ai.used", {"a": 1}, 3, 0.05)

        return asyncio.get_running_loop().time() - started

    assert asyncio.run(timed()) < 0.5
    assert len(tries) == 1 and tries[0] <= 0.05
