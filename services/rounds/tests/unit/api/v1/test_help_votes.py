"""Votes on the help chat's answers (routers/help_votes.py): only the page that got an answer can
vote on it, one vote an answer, changed or cleared; sent on to Langfuse on the answer's trace.
The table's side is in tests/integration/test_help_votes.py."""

import json
import uuid

import pytest
from fake_redis import FakeRedis

from rounds.api.v1 import help_votes as routes
from rounds.config import settings
from rounds.helpers.help_replies import help_signing_key, vote_signature
from rounds.repositories import help_votes
from tests.unit.api.v1.test_help import CATALOG, fake_catalog

ANSWER = uuid.uuid4()
TRACE = "a" * 32


@pytest.fixture
def stored(monkeypatch):
    """The votes table in memory, and the votes sent on to Langfuse, by trace."""
    votes = {}
    mirrored = []

    async def save(answer_id, trace_id, vote):
        if vote is None:
            votes.pop(answer_id, None)
        else:
            votes[answer_id] = (trace_id, vote)

    async def mirror(trace_id, current):
        mirrored.append(trace_id)

    monkeypatch.setattr(help_votes, "save", save)
    monkeypatch.setattr(routes, "mirror_vote", mirror)
    monkeypatch.setattr(routes, "get_redis", lambda: FakeRedis())

    return votes, mirrored


def vote(client, value, answer=ANSWER, trace=TRACE, signature=None):
    body = {
        "trace_id": trace,
        "signature": signature
        or vote_signature(answer, trace, help_signing_key(settings.service_secret)),
        "value": value,
    }

    return client.put(f"/help/answers/{answer}/vote", json=body)


def test_a_visitor_votes_changes_and_clears_their_vote(client, stored):
    votes, mirrored = stored

    assert vote(client, 1).status_code == 204
    assert votes == {ANSWER: (TRACE, 1)}
    assert vote(client, -1).status_code == 204
    assert votes == {ANSWER: (TRACE, -1)}
    assert vote(client, None).status_code == 204
    assert votes == {}
    # Each change goes on to the answer's Langfuse trace.
    assert mirrored == [TRACE, TRACE, TRACE]


def test_an_answer_without_a_trace_keeps_its_vote_and_sends_nothing_on(client, stored):
    votes, mirrored = stored

    assert vote(client, 1, trace=None).status_code == 204
    assert votes == {ANSWER: (None, 1)}
    assert mirrored == [None]


@pytest.mark.parametrize(
    "change",
    [
        {"signature": "0" * 64},
        # Another answer's signature, or another trace's.
        {
            "signature": vote_signature(
                uuid.uuid4(), TRACE, help_signing_key(settings.service_secret)
            )
        },
        {"signature": vote_signature(ANSWER, "b" * 32, help_signing_key(settings.service_secret))},
        {"trace": "b" * 32},
        {"trace": None},
    ],
)
def test_a_vote_without_the_answers_own_signature_is_refused(client, stored, change):
    votes, mirrored = stored
    signature = change.get("signature") or vote_signature(
        ANSWER, TRACE, help_signing_key(settings.service_secret)
    )

    refused = vote(client, 1, trace=change.get("trace", TRACE), signature=signature)

    assert refused.status_code == 404
    assert refused.json()["detail"] == "There's no such answer."
    assert (votes, mirrored) == ({}, [])


@pytest.mark.parametrize("value", [0, 2, "up"])
def test_only_a_thumbs_up_or_down_is_taken(client, stored, value):
    assert vote(client, value).status_code == 422
    assert stored == ({}, [])


def test_with_langfuse_the_answer_names_the_trace_its_model_call_reports_to(client, monkeypatch):
    trace_ids = []

    async def fake_stream(messages, used=None, trace_id=None, session_id=None):
        trace_ids.append(trace_id)
        yield "Paste it."

    monkeypatch.setattr("rounds.api.v1.help.billing.catalog", fake_catalog(CATALOG))
    monkeypatch.setattr("rounds.api.v1.help.stream_reply", fake_stream)
    monkeypatch.setattr("rounds.api.v1.help.new_trace_id", lambda: TRACE)

    response = client.post("/help/chat", json={"messages": [{"role": "user", "content": "Hi"}]})
    done = json.loads(response.text.strip().split("\n\n")[-1][6:])

    assert trace_ids == [TRACE]
    assert done["answer"]["trace_id"] == TRACE
    expected = vote_signature(
        uuid.UUID(done["answer"]["id"]), TRACE, help_signing_key(settings.service_secret)
    )
    assert done["answer"]["signature"] == expected


def test_votes_past_an_addresss_hourly_limit_are_refused(client, stored, monkeypatch):
    votes, _ = stored
    redis = FakeRedis()
    redis.limits["HELP_VOTES_PER_IP_HOUR"] = 2
    monkeypatch.setattr(routes, "get_redis", lambda: redis)

    assert [vote(client, 1).status_code for _ in range(3)] == [204, 204, 429]
    assert votes == {ANSWER: (TRACE, 1)}
