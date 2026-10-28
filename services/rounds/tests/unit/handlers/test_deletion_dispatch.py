"""Rounds' events route: deletions reach their handlers, other events are ignored, and an
event no retry can handle is acknowledged rather than delivered again."""

import uuid

import pytest
from event_pushes import failing_handler, push
from fastapi.testclient import TestClient

from rounds.api.v1 import events
from rounds.main import app
from rounds.services import session_removal


@pytest.fixture
def removed(monkeypatch):
    calls = []

    async def remove_interview(set_id):
        calls.append(("interview", set_id))

    async def remove_company(company_id):
        calls.append(("company", company_id))

    monkeypatch.setattr(session_removal, "remove_interview", remove_interview)
    monkeypatch.setattr(session_removal, "remove_company", remove_company)

    return calls


def test_deletions_reach_their_handlers_and_other_events_are_ignored(client, removed):
    company_id, set_id = uuid.uuid4(), uuid.uuid4()
    interview = {"interview_id": str(uuid.uuid4()), "company_id": str(company_id)}

    for event_type, data in [
        ("interview.deleted", {**interview, "set_id": str(set_id), "extra": 1}),
        ("company.deleted", {"company_id": str(company_id)}),
        ("answer.recorded", {"question_id": "q"}),
    ]:
        assert client.post("/internal/events", json=push(event_type, data)).status_code == 204

    assert removed == [("interview", set_id), ("company", company_id)]


@pytest.mark.parametrize("data", [{}, {"company_id": "not-a-uuid"}, {"company_id": None}])
def test_a_malformed_deletion_is_acknowledged_not_retried(client, removed, data):
    response = client.post("/internal/events", json=push("company.deleted", data))

    assert response.status_code == 204
    assert removed == []


def test_a_failing_deletion_answers_an_error_for_pub_sub_to_retry(monkeypatch):
    """A database outage isn't the event's fault: Pub/Sub delivers it again."""
    failing_handler(monkeypatch, events, ConnectionError("database down"))

    response = TestClient(app, raise_server_exceptions=False).post(
        "/internal/events", json=push("company.deleted", {"company_id": str(uuid.uuid4())})
    )

    assert response.status_code == 500
