"""Tests never publish to Pub/Sub: the local stack's emulator would push their events to the
running services, which would act on the tests' made-up rows. The one set of fixtures every
service's tests import (each service's pytest `pythonpath` includes this folder), in its
tests/conftest.py, so unit and integration tests alike are covered:

    from no_publishing import no_publishing, published  # noqa: F401

`published` keeps what was published, as (type, data), for a test to read; `no_publishing` (autouse)
turns it on for every test and fails a test whose code reached Pub/Sub's publish endpoint anyway,
past `pubsub.publish_batch`."""

import base64
import json

import httpx
import pytest
from testee_common.events import pubsub


def publishes(request: httpx.Request) -> bool:
    """A call to Pub/Sub's publish endpoint, the emulator's or Google's."""
    return "/topics/" in request.url.path and request.url.path.endswith(":publish")


@pytest.fixture
def published(monkeypatch):
    """The events published, as (type, data); nothing reaches Pub/Sub."""
    sent = []

    async def publish_batch(messages, timeout=None):
        for message in messages:
            data = json.loads(base64.b64decode(message["data"]))
            sent.append((message["attributes"]["type"], data))

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)

    return sent


@pytest.fixture(autouse=True)
def no_publishing(monkeypatch, published):
    """Every test publishes into `published`; a call that still heads for Pub/Sub is stopped and
    fails the test, so a new way of publishing can't leak events into the running stack."""
    reached = []
    send = httpx.AsyncClient.send
    send_now = httpx.Client.send

    async def guarded(client, request, *args, **kwargs):
        if publishes(request):
            reached.append(str(request.url))

            raise RuntimeError("Tests never publish to Pub/Sub")

        return await send(client, request, *args, **kwargs)

    def guarded_now(client, request, *args, **kwargs):
        if publishes(request):
            reached.append(str(request.url))

            raise RuntimeError("Tests never publish to Pub/Sub")

        return send_now(client, request, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "send", guarded)
    monkeypatch.setattr(httpx.Client, "send", guarded_now)

    yield published

    if reached:
        pytest.fail(f"The test published to Pub/Sub: {reached}")
