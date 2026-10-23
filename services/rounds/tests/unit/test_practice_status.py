import uuid
from types import SimpleNamespace

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.helpers.practice import practice_statuses
from app.main import app
from app.storage import practice_sessions

TEMPLATE = uuid.uuid4()


@pytest.fixture(autouse=True)
def signed_in():
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True
    )
    yield
    app.dependency_overrides.clear()


def topic(answered, total=3, status="in_progress", template_id=TEMPLATE):
    """A section of the latest round: `answered` of its `total` questions answered."""
    return SimpleNamespace(
        interview_set_id=template_id,
        status=status,
        answers=[object()] * answered,
        questions=[{}] * total,
    )


def status_of(*topics):
    return [
        (item.status, item.topics_done, item.topics_total) for item in practice_statuses(topics)
    ]


def test_one_topic_started_and_unfinished_is_in_progress_even_once_the_round_ended():
    # The round ended (every section finished) with one topic only partly answered.
    assert status_of(topic(1, status="finished"), topic(0, status="finished")) == [
        ("in_progress", 0, 2)
    ]


def test_one_topic_answered_to_the_end_of_several_is_in_progress():
    assert status_of(topic(3, status="finished"), topic(0), topic(0)) == [("in_progress", 1, 3)]


def test_every_topic_answered_to_the_end_is_completed():
    assert status_of(topic(3, status="finished"), topic(2, total=2)) == [("completed", 2, 2)]


def test_a_round_without_an_answer_is_not_started():
    assert status_of(topic(0), topic(0)) == []
    assert practice_statuses([]) == []


def test_each_template_has_its_own_status():
    other = uuid.uuid4()
    statuses = practice_statuses([topic(1), topic(3, template_id=other)])

    assert {item.template_id: item.status for item in statuses} == {
        TEMPLATE: "in_progress",
        other: "completed",
    }


def test_the_list_gives_the_signed_in_talents_statuses(client, monkeypatch):
    asked = []

    async def fake_rounds(user_id):
        asked.append(user_id)

        return [topic(3)]

    monkeypatch.setattr(practice_sessions, "latest_rounds", fake_rounds)

    response = client.get("/practice/statuses")

    assert asked == ["ann"]
    assert response.json() == [
        {"template_id": str(TEMPLATE), "status": "completed", "topics_done": 1, "topics_total": 1}
    ]


def test_signed_out_there_are_no_statuses(client):
    app.dependency_overrides.clear()

    assert client.get("/practice/statuses").status_code == 401
