from fastapi.testclient import TestClient
from prepza_common.limits.limit_list import LIMITS

from app.main import app
from app.routers import sizes


def answer(monkeypatch, redis):
    monkeypatch.setattr(sizes, "get_redis", lambda: redis)

    return TestClient(app).get("/sizes")


def test_anyone_reads_the_questions_per_topic_set_in_controls(monkeypatch, redis):
    redis.limits["INTERVIEW_QUESTIONS_PER_TOPIC"] = "7"

    response = answer(monkeypatch, redis)

    # Public: no sign-in.
    assert response.status_code == 200
    assert response.json() == {"questions_per_topic": 7}


def test_unchanged_in_controls_it_is_the_default(monkeypatch, redis):
    response = answer(monkeypatch, redis)

    default = LIMITS["INTERVIEW_QUESTIONS_PER_TOPIC"].default
    assert response.json() == {"questions_per_topic": default}
