import pytest
from fastapi import HTTPException

import rounds.api.v1.help as help_routes
from rounds.config import settings


@pytest.fixture
def checks(monkeypatch):
    """The "I'm not a robot" check, on, recording the requests asked for it; refusing when
    "refuse" is set."""
    state = {"asked": [], "refuse": False}

    async def require_human(request, secret):
        state["asked"].append(request.url.path)

        if state["refuse"]:
            raise HTTPException(403, "Confirm you're not a robot, then try again.")

    async def nothing(*args):
        return None

    monkeypatch.setattr(settings, "turnstile_secret_key", "s3cret")
    monkeypatch.setattr(help_routes, "require_human", require_human)
    monkeypatch.setattr(help_routes.contact_service.sessions, "add_event", nothing)
    monkeypatch.setattr(help_routes.contact_service.outbox_service, "flush_quietly", nothing)

    return state


def test_a_contact_message_is_asked_and_one_that_fails_isnt_sent(client, checks, monkeypatch):
    saved = []

    async def save(session, event_type, data):
        saved.append(data)

    monkeypatch.setattr(help_routes.contact_service.sessions, "add_event", save)
    checks["refuse"] = True
    body = {"name": "Ann", "email": "ann@example.com", "message": "Do you offer invoices?"}

    assert client.post("/help/contact", json=body).status_code == 403
    assert checks["asked"] == ["/help/contact"]
    assert saved == []
