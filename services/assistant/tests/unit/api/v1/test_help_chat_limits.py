"""The help chat's limits (per account, per address, for everyone, the day's tokens and the cap
on unpaid AI spend) and its "I'm not a robot" check on a visitor's first question."""

import pytest
from fastapi import HTTPException
from firebase_admin import auth as firebase_auth
from prepza_common.ai import ai_cap
from prepza_common.ai.ai_constants import AI_PAUSED_TODAY, LIMIT_HIT, MICRO
from prepza_common.config.constants import RATE_LIMITED
from prepza_common.limits.limit_list import LIMITS

from assistant.config import settings
from assistant.constants.help_chat import HELP_ALL_KEY, HELP_SPEND_KEY
from assistant.helpers.help_replies import help_signing_key, reply_signature
from assistant.services import help_answers
from tests.unit.help_setup import BODY

SIGNED_IN = {"Authorization": "Bearer token"}
QUESTION = BODY["messages"][0]


@pytest.fixture
def model(monkeypatch):
    """The model's answers, counted; a signed-in user u1 for requests that send a token."""
    asked = []

    async def answer(messages, used, trace_id=None, session_id=None):
        asked.append(1)
        yield "Paste a job description."

    monkeypatch.setattr(help_answers, "stream_reply", answer)
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


def test_accounts_addresses_and_the_daily_total_are_counted(client, help_redis, model):
    client.post("/help/chat", json=BODY)
    # Behind Google's load balancer: the visitor's own header, then their address and the
    # balancer's.
    forwarded = {"X-Forwarded-For": "1.1.1.1, 203.0.113.7, 35.191.0.1"}
    client.post("/help/chat", json=BODY, headers={**SIGNED_IN, **forwarded})

    counted = {key: count for key, count in help_redis.counts.items() if key.startswith("rate:")}
    assert counted == {
        "rate:help:ip:testclient": 1,
        "rate:help:all": 2,
        "rate:help:u1": 1,
        "rate:help:ip:203.0.113.7": 1,
    }


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
    client, help_redis, published, model, name, key, whose, edited
):
    value = current(help_redis, name, edited)
    # Everything up to the last one the limit allows was used today.
    help_redis.counts[key] = value - 1

    last = client.post("/help/chat", json=BODY, headers=SIGNED_IN)
    refused = client.post("/help/chat", json=BODY, headers=SIGNED_IN)

    assert last.status_code == 200
    assert refused.status_code == 429
    assert refused.json()["detail"] == RATE_LIMITED
    assert len(model) == 1
    assert hits(published) == [(name, whose)]


@pytest.mark.parametrize("edited", [False, True])
def test_the_chat_is_paused_once_todays_unpaid_ai_spend_reaches_the_cap(
    client, help_redis, published, model, edited
):
    cap = current(help_redis, "AI_SPEND_UNPAID_DAY", edited)
    help_redis.counts[ai_cap.today_key()] = int(cap * MICRO) - 1

    under = client.post("/help/chat", json=BODY, headers=SIGNED_IN)
    help_redis.counts[ai_cap.today_key()] = int(cap * MICRO)
    capped = client.post("/help/chat", json=BODY, headers=SIGNED_IN)

    assert under.status_code == 200
    assert capped.status_code == 503
    assert capped.json()["detail"] == AI_PAUSED_TODAY
    assert len(model) == 1
    assert hits(published) == [("AI_SPEND_UNPAID_DAY", "u1")]


def test_a_visitor_is_asked_until_their_chat_has_a_reply(client, monkeypatch, help_redis, model):
    """A reply is signed only after the check, so a made-up one doesn't skip it."""
    asked = []

    async def require_human(request, secret):
        asked.append(request.url.path)

    monkeypatch.setattr(settings, "turnstile_secret_key", "s3cret")
    monkeypatch.setattr(help_answers, "require_human", require_human)
    reply = {"role": "assistant", "content": "Paste it."}
    signed = {
        **reply,
        "signature": reply_signature("Paste it.", help_signing_key(settings.service_secret)),
    }

    client.post("/help/chat", json={"messages": [QUESTION]})
    client.post("/help/chat", json={"messages": [QUESTION, signed, QUESTION]})

    assert asked == ["/help/chat"]

    client.post("/help/chat", json={"messages": [QUESTION, reply, QUESTION]})

    assert asked == ["/help/chat", "/help/chat"]


def test_a_visitor_who_fails_the_check_gets_no_answer(client, monkeypatch, help_redis, model):
    async def refuse(request, secret):
        raise HTTPException(403, "Confirm you're not a robot, then try again.")

    monkeypatch.setattr(help_answers, "require_human", refuse)

    refused = client.post("/help/chat", json=BODY)

    assert refused.status_code == 403
    assert refused.json()["detail"] == "Confirm you're not a robot, then try again."
    assert model == []
