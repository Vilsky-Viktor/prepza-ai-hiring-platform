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

os.environ.setdefault("COMPANIES_URL", "http://companies")
os.environ.setdefault("BILLING_URL", "http://billing")
os.environ.setdefault("LIBRARY_URL", "http://library")
os.environ.setdefault("NOTIFICATIONS_URL", "http://notifications")
os.environ.setdefault("ATS_URL", "http://ats")
os.environ.setdefault("API_URL", "http://api")
os.environ.setdefault("ROUNDS_URL", "http://rounds")
os.environ.setdefault("ACCOUNTS_URL", "http://accounts")
os.environ.setdefault("SITE_SERVICE_URL", "http://site")

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "demo-test")
os.environ.setdefault("SITE_URL", "http://localhost:8090")
os.environ.setdefault("FIREBASE_WEB_API_KEY", "demo-api-key")

import pytest
from fastapi.testclient import TestClient
from no_publishing import no_publishing, published  # noqa: F401
from prepza_common.redis import memory_cache

from assistant.main import app


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
