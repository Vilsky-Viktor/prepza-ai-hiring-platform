import base64
import json

import pytest
from prepza_common.events import pubsub
from prepza_common.redis import memory_cache


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    """Each test reads the limits afresh, not a value an earlier test cached."""
    monkeypatch.setattr(memory_cache, "_entries", {})


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
