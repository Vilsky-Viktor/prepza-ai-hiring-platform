import uuid

import pytest
from fake_redis import FakeRedis
from prepza_common.ai.ai_constants import LIMIT_HIT
from prepza_common.http.http import bearer
from prepza_common.limits.limit_list import LIMITS

from library.repositories import bank, feedback
from tests.unit.api.v1.test_internal import token

QUESTION_ID = uuid.uuid4()
AUTH = bearer(token())


@pytest.fixture(autouse=True)
def redis(monkeypatch):
    """Rate limits count in memory."""
    fake = FakeRedis()
    monkeypatch.setattr("library.services.question_feedback.get_redis", lambda: fake)

    return fake


@pytest.fixture(autouse=True)
def left_bank(monkeypatch):
    """The questions a report took out of the shared bank."""
    left = []

    async def fake_leave(session, question_ids):
        left.extend(question_ids)

    monkeypatch.setattr(bank, "leave", fake_leave)

    return left


async def not_reported(session, question_id, user_id):
    return False


def test_a_candidates_second_report_is_rejected(client, monkeypatch, left_bank):
    reported = set()

    async def fake_report(session, question_id, user_id, reason, comment):
        if (question_id, user_id) in reported:
            return False

        reported.add((question_id, user_id))

        return True

    async def fake_has_reported(session, question_id, user_id):
        return (question_id, user_id) in reported

    async def fake_review(question_id):
        pass

    monkeypatch.setattr(feedback, "report_question", fake_report)
    monkeypatch.setattr(feedback, "has_reported", fake_has_reported)
    monkeypatch.setattr("library.services.question_feedback.review", fake_review)
    url = f"/internal/questions/{QUESTION_ID}/reports"
    body = {"user_id": "ann", "reason": "unclear"}

    assert client.get(f"{url}/mine", params={"user_id": "ann"}, headers=AUTH).json() == {
        "reported": False
    }
    assert client.post(url, json=body, headers=AUTH).status_code == 201
    assert client.post(url, json=body, headers=AUTH).status_code == 409
    # Reported, it left the shared bank once; the refused second report changed nothing.
    assert left_bank == [QUESTION_ID]
    assert client.get(f"{url}/mine", params={"user_id": "ann"}, headers=AUTH).json() == {
        "reported": True
    }


def test_a_question_reported_as_hard_to_read_is_saved_with_that_reason(client, monkeypatch):
    saved = []

    async def fake_report(session, question_id, user_id, reason, comment):
        saved.append((question_id, user_id, reason))

        return True

    async def fake_review(question_id):
        pass

    monkeypatch.setattr(feedback, "report_question", fake_report)
    monkeypatch.setattr(feedback, "has_reported", not_reported)
    monkeypatch.setattr("library.services.question_feedback.review", fake_review)
    url = f"/internal/questions/{QUESTION_ID}/reports"
    body = {"user_id": "ann", "reason": "hard_to_read"}

    assert client.post(url, json=body, headers=AUTH).status_code == 201
    assert saved == [(QUESTION_ID, "ann", "hard_to_read")]


@pytest.mark.parametrize("edited", [None, 2])
def test_a_users_reports_are_limited_a_day(client, monkeypatch, redis, published, edited):
    """At the limit's edited value, or its default when it isn't edited."""
    allowed = edited or LIMITS["REPORTS_PER_DAY"].default

    if edited:
        redis.limits["REPORTS_PER_DAY"] = str(edited)

    async def fake_report(session, question_id, user_id, reason, comment):
        return True

    async def fake_review(question_id):
        pass

    monkeypatch.setattr(feedback, "report_question", fake_report)
    monkeypatch.setattr(feedback, "has_reported", not_reported)
    monkeypatch.setattr("library.services.question_feedback.review", fake_review)
    body = {"user_id": "spammer", "reason": "unclear"}

    for _ in range(allowed):
        url = f"/internal/questions/{uuid.uuid4()}/reports"
        assert client.post(url, json=body, headers=AUTH).status_code == 201

    url = f"/internal/questions/{uuid.uuid4()}/reports"
    assert client.post(url, json=body, headers=AUTH).status_code == 429
    assert [(event, data["limit"], data["user_id"]) for event, data in published] == [
        (LIMIT_HIT, "REPORTS_PER_DAY", "spammer")
    ]
