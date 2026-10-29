"""Pub/Sub's pushes: accounts' `user.deleted` deletes generation's part of the account; an
event no retry can handle is acknowledged (204) once, a failure a retry may fix answers 500."""

import pytest
from event_pushes import failing_handler, push
from fastapi.testclient import TestClient

from generation.api.v1 import events
from generation.handlers import user_deleted
from generation.main import app


def test_a_deleted_account_is_deleted_here_and_other_events_are_ignored(monkeypatch):
    deleted = []

    async def delete_user(user_id):
        deleted.append(user_id)

    monkeypatch.setattr(user_deleted.accounts, "delete_user", delete_user)
    client = TestClient(app)
    gone = push("user.deleted", {"user_id": "ann", "email": "ann@example.com"})

    assert client.post("/internal/events", json=gone).status_code == 204
    assert client.post("/internal/events", json=push("company.deleted", {})).status_code == 204
    assert deleted == ["ann"]


@pytest.mark.parametrize("data", [{}, {"user_id": 7}])
def test_an_event_no_retry_can_handle_is_acknowledged(data):
    assert (
        TestClient(app).post("/internal/events", json=push("user.deleted", data)).status_code == 204
    )


def test_an_event_a_retry_may_handle_is_answered_with_an_error(monkeypatch):
    failing_handler(monkeypatch, events, ConnectionError("The database went away"))
    client = TestClient(app, raise_server_exceptions=False)

    assert client.post("/internal/events", json=push("user.deleted", {})).status_code == 500
