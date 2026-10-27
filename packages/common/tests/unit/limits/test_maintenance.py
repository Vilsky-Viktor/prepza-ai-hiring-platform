import asyncio
import time
from datetime import UTC, datetime

import pytest
from fake_redis import DownRedis, FakeRedis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prepza_common.auth.user import User
from prepza_common.config.constants import (
    MAINTENANCE,
    MAINTENANCE_CACHE_SECONDS,
    MAINTENANCE_KEY,
    MAINTENANCE_STARTED_KEY,
)
from prepza_common.i18n.translations import TRANSLATIONS
from prepza_common.limits import maintenance
from prepza_common.limits.maintenance import (
    MaintenanceMiddleware,
    is_on,
    put_back_start,
    set_on,
    take_start,
)
from prepza_common.redis import memory_cache

REDIS = FakeRedis()
app = FastAPI()
app.add_middleware(MaintenanceMiddleware, get_redis=lambda: REDIS)

PATHS = [
    "/companies",
    "/sessions/1/answers",
    "/health",
    "/ready",
    "/maintenance",
    "/superadmin/maintenance",
    "/internal/events",
    "/internal/schedules/outbox",
    "/webhooks/paddle",
    "/webhooks/resend",
    # Unsubscribing must always work, and the legal texts stay readable.
    "/unsubscribe/token-1",
    "/help/legal/privacy",
]
OPEN = PATHS[2:]

for path in PATHS:
    app.add_api_route(path, lambda: {"ok": True}, methods=["GET", "POST"])

client = TestClient(app)


@pytest.fixture(autouse=True)
def switched_on(monkeypatch):
    """On, with ann as the only superadmin; a token is the email it signs in. Nothing cached."""
    REDIS.counts = {MAINTENANCE_KEY: "ann"}
    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    monkeypatch.setattr(
        maintenance,
        "verify",
        lambda token: User(
            uid=token, email=token, email_verified=True, sign_in_provider="google.com"
        ),
    )


def test_every_other_request_gets_a_translated_503():
    for path in PATHS[:2]:
        refused = client.post(path, headers={"Accept-Language": "uk"})

        assert refused.status_code == 503
        assert refused.json()["detail"] == TRANSLATIONS["uk"][MAINTENANCE]

    assert client.get("/companies").json()["detail"] == MAINTENANCE


def test_health_the_switch_internal_calls_and_webhooks_stay_open():
    for path in OPEN:
        assert client.post(path).status_code == 200


def test_a_superadmin_passes_and_others_signed_in_do_not():
    superadmin = {"Authorization": "Bearer ann@example.com"}

    assert client.get("/companies", headers=superadmin).status_code == 200

    other = {"Authorization": "Bearer bob@example.com"}

    assert client.get("/companies", headers=other).status_code == 503


def test_an_invalid_token_is_refused(monkeypatch):
    monkeypatch.setattr(maintenance, "verify", lambda token: None)

    assert client.get("/companies", headers={"Authorization": "Bearer x"}).status_code == 503


def test_off_everything_passes():
    REDIS.counts = {}

    assert client.get("/companies").status_code == 200


def test_with_redis_down_it_is_off(monkeypatch):
    assert not asyncio.run(is_on(DownRedis()))

    monkeypatch.setitem(globals(), "REDIS", DownRedis())

    assert client.get("/companies").status_code == 200


def test_the_switch_turns_on_and_off_and_remembers_who():
    redis = FakeRedis()

    asyncio.run(set_on(redis, True, "ann"))

    assert redis.counts[MAINTENANCE_KEY] == "ann"
    assert asyncio.run(is_on(redis))

    asyncio.run(set_on(redis, False, "ann"))

    assert not asyncio.run(is_on(redis))


def test_each_instance_reads_the_switch_at_most_every_few_seconds(monkeypatch):
    now = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: now)

    assert asyncio.run(is_on(REDIS))

    REDIS.counts = {}

    assert asyncio.run(is_on(REDIS))

    monkeypatch.setattr(time, "monotonic", lambda: now + MAINTENANCE_CACHE_SECONDS + 1)

    assert not asyncio.run(is_on(REDIS))


def test_the_message_has_translations():
    for language in TRANSLATIONS.values():
        assert MAINTENANCE in language


def test_it_remembers_when_it_was_turned_on_and_gives_that_out_once():
    redis = FakeRedis()
    before = datetime.now(UTC)

    asyncio.run(set_on(redis, True, "ann"))
    first = redis.counts[MAINTENANCE_STARTED_KEY]
    # Turned on again while on: still the first start.
    asyncio.run(set_on(redis, True, "bob"))

    assert redis.counts[MAINTENANCE_STARTED_KEY] == first

    started = asyncio.run(take_start(redis))

    assert started >= before
    assert asyncio.run(take_start(redis)) is None

    asyncio.run(put_back_start(redis, started))

    assert asyncio.run(take_start(redis)) == started
