import os

# Integration tests (tests/integration) use a database of their own, never the dev one: the
# service's database name with "_test" added.
if os.getenv("INTEGRATION_TESTS"):
    os.environ["DATABASE_URL"] += "_test"

os.environ.setdefault("FIREBASE_PROJECT_ID", "demo-test")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("COMPANIES_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("API_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("OPENAI_API_KEY", "test")

for name in ("companies", "billing", "library", "notifications", "ats", "api", "rounds"):
    os.environ.setdefault(f"{name.upper()}_URL", f"http://{name}")

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "demo-test")
os.environ.setdefault("SITE_URL", "http://localhost:8090")
os.environ.setdefault("FIREBASE_WEB_API_KEY", "demo-api-key")

import base64
import json

import pytest
from fastapi.testclient import TestClient
from prepza_common import memory_cache, pubsub

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def clean_process(monkeypatch):
    """Every test starts clean: nothing an earlier test kept in this process's memory cache, and
    no route override left behind."""
    monkeypatch.setattr(memory_cache, "_entries", {})

    yield

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def published(monkeypatch):
    """The events published (AI calls and limit hits recorded), as (type, data); nothing reaches
    Pub/Sub, so the running stack's billing never stores a test's."""
    sent = []

    async def publish_batch(messages, timeout=None):
        for message in messages:
            data = json.loads(base64.b64decode(message["data"]))
            sent.append((message["attributes"]["type"], data))

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)

    return sent
