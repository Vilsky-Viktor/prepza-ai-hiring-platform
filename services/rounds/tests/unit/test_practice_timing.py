import uuid
from types import SimpleNamespace

import pytest

from app.integrations import library
from app.main import app
from app.storage import practice_sessions, sessions

# signed_in: the talent signed in, for every test here as in test_practice.py.
from tests.unit.test_practice import TEMPLATE_ID, content, signed_in  # noqa: F401

# How long a practice round's questions take: the times to choose from, and the one chosen.


def test_anyone_sees_how_many_questions_a_round_has(client, monkeypatch, redis):
    async def fake_content(template_id):
        two_topics = content(14)
        two_topics["topics"].append({**content(4)["topics"][0], "title": "SQL"})

        return two_topics

    monkeypatch.setattr(library, "practice_content", fake_content)
    app.dependency_overrides.clear()
    redis.limits["QUESTION_SECONDS_MEDIUM"] = 40
    template_id = uuid.uuid4()
    size = {
        "questions": 14,
        # The times per question to choose from, worked out from the level's seconds.
        "timings": [
            {"id": "standard", "seconds": 40},
            {"id": "double", "seconds": 80},
            {"id": "untimed", "seconds": None},
        ],
    }

    # Ten of the first topic's 14, and all 4 of the second.
    assert client.get(f"/practice/{template_id}/size").json() == size

    async def unreachable(template_id):
        raise AssertionError("asked library again")

    monkeypatch.setattr(library, "practice_content", unreachable)

    # Kept for a while: library isn't asked again.
    assert client.get(f"/practice/{template_id}/size").json() == size


@pytest.mark.parametrize(
    ("body", "seconds", "preview"),
    [(None, 40, False), ({"timing": "double"}, 80, True), ({"timing": "untimed"}, None, True)],
)
def test_a_talent_chooses_the_time_per_question(client, monkeypatch, redis, body, seconds, preview):
    """More time or none for whoever needs it (WCAG 2.2.1); such a round, as a repeat, measures
    something else, so it doesn't count in the questions' statistics."""
    redis.limits["QUESTION_SECONDS_MEDIUM"] = 40
    created = []

    async def fake_content(template_id):
        return content(10)

    async def fake_create(user_id, round_id, topics, seconds, preview=False, practice=False):
        created.append((seconds, preview))

        return [SimpleNamespace(id=uuid.uuid4())]

    async def fake_practiced(user_id, template_id):
        return False

    monkeypatch.setattr(library, "practice_content", fake_content)
    monkeypatch.setattr(sessions, "create_many", fake_create)
    monkeypatch.setattr(practice_sessions, "practiced", fake_practiced)

    assert client.post(f"/practice/{TEMPLATE_ID}", json=body).status_code == 201
    assert created == [(seconds, preview)]


def test_an_unknown_timing_is_refused(client, monkeypatch, redis):
    assert client.post(f"/practice/{TEMPLATE_ID}", json={"timing": "triple"}).status_code == 422
