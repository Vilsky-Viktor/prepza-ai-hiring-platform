import pytest
from firebase_admin import auth as firebase_auth
from prepza_common.ai import ai_cap
from prepza_common.ai.ai_constants import AI_PAUSED_TODAY, LIMIT_HIT, MICRO
from prepza_common.config.constants import RATE_LIMITED
from prepza_common.limits.limit_list import LIMITS

import rounds.api.v1.help as help_routes
from rounds.constants.help import HELP_ALL_KEY, HELP_SPEND_KEY
from tests.unit.api.v1.test_help import CATALOG, fake_catalog

BODY = {"messages": [{"role": "user", "content": "How do I start?"}]}
SIGNED_IN = {"Authorization": "Bearer token"}
CONTACT = {"name": "Ann", "email": "ann@example.com", "message": "Do you offer invoices?"}


@pytest.fixture(autouse=True)
def model(monkeypatch):
    """The model's answers, counted; a signed-in user u1 for requests that send a token."""
    asked = []

    async def answer(messages, used, run_id=None, session_id=None):
        asked.append(1)
        yield "Paste a job description."

    async def nothing(*args):
        return None

    monkeypatch.setattr(help_routes.billing, "catalog", fake_catalog(CATALOG))
    monkeypatch.setattr(help_routes, "stream_reply", answer)
    monkeypatch.setattr(help_routes.contact_service.sessions, "add_event", nothing)
    monkeypatch.setattr(help_routes.contact_service.outbox_service, "flush_quietly", nothing)
    monkeypatch.setattr(firebase_auth, "verify_id_token", lambda token, **_: {"uid": "u1"})

    return asked


def current(redis, name: str, edited: bool) -> int:
    """The limit's value: an edited one (in Redis, as the Controls tab saves it), or its
    default."""
    if not edited:
        return LIMITS[name].default

    value = LIMITS[name].lowest + 1
    redis.limits[name] = value

    return value


def hits(published) -> list[tuple]:
    return [(data["limit"], data["user_id"]) for kind, data in published if kind == LIMIT_HIT]


@pytest.mark.parametrize("edited", [False, True])
@pytest.mark.parametrize(
    ("name", "key", "whose"),
    [
        ("HELP_USER_LIMIT", "rate:help:u1", "u1"),
        # An address's limit is no user's.
        ("HELP_IP_LIMIT", "rate:help:ip:testclient", None),
        ("HELP_DAILY_LIMIT", HELP_ALL_KEY, "u1"),
        # Tokens: the answer that reaches the budget is kept, the next question refused.
        ("HELP_TOKENS_PER_DAY", HELP_SPEND_KEY, "u1"),
    ],
)
def test_each_help_chat_limit_refuses_past_its_current_value(
    client, redis, published, model, name, key, whose, edited
):
    value = current(redis, name, edited)
    # Everything up to the last one the limit allows was used today.
    redis.counts[key] = value - 1

    last = client.post("/help/chat", json=BODY, headers=SIGNED_IN)
    refused = client.post("/help/chat", json=BODY, headers=SIGNED_IN)

    assert last.status_code == 200
    assert refused.status_code == 429
    assert refused.json()["detail"] == RATE_LIMITED
    assert len(model) == 1
    assert hits(published) == [(name, whose)]


@pytest.mark.parametrize("edited", [False, True])
@pytest.mark.parametrize(
    ("name", "key"),
    [
        ("CONTACT_IP_LIMIT", "rate:contact:ip:testclient"),
        ("CONTACT_DAILY_LIMIT", "rate:contact:all"),
    ],
)
def test_each_contact_limit_refuses_past_its_current_value(
    client, redis, published, name, key, edited
):
    value = current(redis, name, edited)
    redis.counts[key] = value - 1

    last = client.post("/help/contact", json=CONTACT)
    refused = client.post("/help/contact", json=CONTACT)

    assert last.status_code == 204
    assert refused.status_code == 429
    assert refused.json()["detail"] == RATE_LIMITED
    assert hits(published) == [(name, None)]


@pytest.mark.parametrize("edited", [False, True])
def test_the_chat_is_paused_once_todays_unpaid_ai_spend_reaches_the_cap(
    client, redis, published, model, edited
):
    cap = current(redis, "AI_SPEND_UNPAID_DAY", edited)
    redis.counts[ai_cap.today_key()] = int(cap * MICRO) - 1

    under = client.post("/help/chat", json=BODY, headers=SIGNED_IN)
    redis.counts[ai_cap.today_key()] = int(cap * MICRO)
    capped = client.post("/help/chat", json=BODY, headers=SIGNED_IN)

    assert under.status_code == 200
    assert capped.status_code == 503
    assert capped.json()["detail"] == AI_PAUSED_TODAY
    assert len(model) == 1
    assert hits(published) == [("AI_SPEND_UNPAID_DAY", "u1")]
