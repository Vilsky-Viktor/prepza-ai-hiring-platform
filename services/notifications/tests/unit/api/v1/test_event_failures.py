"""Pub/Sub's pushes: an event no retry can handle is acknowledged (204) once, so Pub/Sub
doesn't deliver it again; a failure a retry may fix answers 500, for Pub/Sub to retry."""

import pytest
from event_pushes import failing_handler, push
from fastapi.testclient import TestClient

from notifications.api.v1 import events
from notifications.main import app


@pytest.mark.parametrize("error", [KeyError("company_id"), ValueError("badly formed UUID")])
def test_an_event_no_retry_can_handle_is_acknowledged(monkeypatch, error):
    failing_handler(monkeypatch, events, error)

    assert (
        TestClient(app).post("/internal/events", json=push("company.deleted", {})).status_code
        == 204
    )


def test_an_event_a_retry_may_handle_is_answered_with_an_error(monkeypatch):
    failing_handler(monkeypatch, events, ConnectionError("The database went away"))
    client = TestClient(app, raise_server_exceptions=False)

    assert client.post("/internal/events", json=push("company.deleted", {})).status_code == 500
