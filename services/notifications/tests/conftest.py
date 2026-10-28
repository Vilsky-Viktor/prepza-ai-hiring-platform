import os

# Integration tests (tests/integration) use a database of their own, never the dev one: the
# service's database name with "_test" added.
if os.getenv("INTEGRATION_TESTS"):
    os.environ["DATABASE_URL"] += "_test"

os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("FIREBASE_PROJECT_ID", "demo-test")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("SITE_URL", "http://localhost:8090")
os.environ.setdefault("COMPANIES_URL", "http://companies")
os.environ.setdefault("SITE_SERVICE_URL", "http://site")
os.environ.setdefault("ACCOUNTS_URL", "http://accounts")
os.environ.setdefault("ROUNDS_URL", "http://rounds")
os.environ.setdefault("BILLING_URL", "http://billing")
os.environ.setdefault("GENERATION_URL", "http://generation")
os.environ.setdefault("EMAIL_LINK_SECRET", "test-email-link-secret")
os.environ.setdefault("PERSON_HASH_KEY", "test-person-hash-key")
os.environ.setdefault("COMPANIES_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("LIBRARY_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("SITE_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("ACCOUNTS_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("BILLING_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
os.environ.setdefault("GENERATION_SERVICE_SECRET", "test-secret-that-is-at-least-32-bytes")
# A demo- project: no Google Cloud, so calls from Pub/Sub, Cloud Tasks and Scheduler aren't
# token-checked, and jobs run locally.
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "demo-test")


import pytest
from fastapi.testclient import TestClient
from no_publishing import no_publishing, published  # noqa: F401
from prepza_common.redis import memory_cache

from notifications.main import app


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
