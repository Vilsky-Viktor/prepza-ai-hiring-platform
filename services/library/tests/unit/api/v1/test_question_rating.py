import uuid

import pytest
from fake_redis import FakeRedis
from prepza_common.ai.ai_constants import LIMIT_HIT
from prepza_common.http.http import bearer
from prepza_common.limits.limit_list import LIMITS

from library.repositories import feedback
from tests.unit.api.v1.test_internal import token

QUESTION_ID = uuid.uuid4()
AUTH = bearer(token())


@pytest.fixture(autouse=True)
def redis(monkeypatch):
    """Rate limits count in memory."""
    fake = FakeRedis()
    monkeypatch.setattr("library.services.question_feedback.get_redis", lambda: fake)

    return fake


def test_a_candidate_rates_a_question_and_reads_it_back(client, monkeypatch):
    stored = {}
    reviewed = []

    async def fake_rate(session, question_id, user_id, value):
        stored[user_id] = value

    async def fake_mine(session, question_id, user_id):
        return stored.get(user_id)

    async def fake_review(question_id):
        reviewed.append(question_id)

    monkeypatch.setattr(feedback, "rate_question", fake_rate)
    monkeypatch.setattr(feedback, "my_question_rating", fake_mine)
    monkeypatch.setattr("library.services.question_feedback.review", fake_review)
    url = f"/internal/questions/{QUESTION_ID}/rating"

    empty = client.get(url, params={"user_id": "ann"}, headers=AUTH)
    put = client.put(url, json={"user_id": "ann", "value": 1}, headers=AUTH)
    again = client.put(url, json={"user_id": "ann", "value": -1}, headers=AUTH)
    saved = client.get(url, params={"user_id": "ann"}, headers=AUTH)

    assert empty.json() == {"value": None}
    assert (put.status_code, again.status_code) == (204, 204)
    assert saved.json() == {"value": -1}
    # Every vote goes to the quality review, which may flag the question.
    assert reviewed == [QUESTION_ID, QUESTION_ID]


@pytest.mark.parametrize("edited", [None, 3])
def test_a_users_ratings_are_limited_a_day(client, monkeypatch, redis, published, edited):
    """At the limit's edited value, or its default when it isn't edited."""
    allowed = edited or LIMITS["RATINGS_PER_DAY"].default

    if edited:
        redis.limits["RATINGS_PER_DAY"] = str(edited)

    async def fake_rate(session, question_id, user_id, value):
        pass

    async def fake_review(question_id):
        pass

    monkeypatch.setattr(feedback, "rate_question", fake_rate)
    monkeypatch.setattr("library.services.question_feedback.review", fake_review)
    body = {"user_id": "voter", "value": 1}

    for _ in range(allowed):
        url = f"/internal/questions/{uuid.uuid4()}/rating"
        assert client.put(url, json=body, headers=AUTH).status_code == 204

    url = f"/internal/questions/{uuid.uuid4()}/rating"
    assert client.put(url, json=body, headers=AUTH).status_code == 429
    assert [(event, data["limit"], data["user_id"]) for event, data in published] == [
        (LIMIT_HIT, "RATINGS_PER_DAY", "voter")
    ]
