import uuid

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.helpers.practice import practice_statuses
from app.main import app
from app.storage import practice_sessions

STARTED, DONE = uuid.uuid4(), uuid.uuid4()


@pytest.fixture(autouse=True)
def signed_in():
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True
    )
    yield
    app.dependency_overrides.clear()


def test_a_template_is_completed_once_every_topic_of_its_latest_round_is_finished():
    statuses = practice_statuses(
        [
            (STARTED, "finished"),
            (STARTED, "in_progress"),
            (STARTED, "finished"),
            (DONE, "finished"),
            (DONE, "finished"),
        ]
    )

    assert [status.model_dump() for status in statuses] == [
        {"template_id": STARTED, "status": "in_progress", "topics_done": 2, "topics_total": 3},
        {"template_id": DONE, "status": "completed", "topics_done": 2, "topics_total": 2},
    ]


def test_a_round_with_no_topic_finished_is_in_progress():
    [status] = practice_statuses([(STARTED, "in_progress"), (STARTED, "in_progress")])

    assert (status.status, status.topics_done, status.topics_total) == ("in_progress", 0, 2)


def test_never_practiced_templates_have_no_status():
    assert practice_statuses([]) == []


def test_the_list_gives_the_signed_in_talents_statuses(client, monkeypatch):
    asked = []

    async def fake_sections(user_id):
        asked.append(user_id)

        return [(DONE, "finished")]

    monkeypatch.setattr(practice_sessions, "latest_round_sections", fake_sections)

    response = client.get("/practice/statuses")

    assert asked == ["ann"]
    assert response.json() == [
        {"template_id": str(DONE), "status": "completed", "topics_done": 1, "topics_total": 1}
    ]


def test_signed_out_there_are_no_statuses(client):
    app.dependency_overrides.clear()

    assert client.get("/practice/statuses").status_code == 401
