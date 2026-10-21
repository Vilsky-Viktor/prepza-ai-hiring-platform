import pytest
from fastapi import HTTPException

import app.routers.help as help_routes
from app.config.settings import settings
from app.helpers.help_replies import help_signing_key, reply_signature
from tests.unit.test_help import CATALOG, fake_catalog

QUESTION = {"role": "user", "content": "How do I start?"}


@pytest.fixture
def checks(monkeypatch):
    """The "I'm not a robot" check, on, recording the requests asked for it; refusing when
    "refuse" is set."""
    state = {"asked": [], "refuse": False}

    async def require_human(request, secret):
        state["asked"].append(request.url.path)

        if state["refuse"]:
            raise HTTPException(403, "Confirm you're not a robot, then try again.")

    async def fake_stream(messages, used=None, run_id=None):
        yield "Paste a job description."

    async def nothing(*args):
        return None

    monkeypatch.setattr(settings, "turnstile_secret_key", "s3cret")
    monkeypatch.setattr(help_routes, "require_human", require_human)
    monkeypatch.setattr(help_routes.billing, "catalog", fake_catalog(CATALOG))
    monkeypatch.setattr(help_routes, "stream_reply", fake_stream)
    monkeypatch.setattr(help_routes.contact_store, "save", nothing)
    monkeypatch.setattr(help_routes.outbox_service, "flush_quietly", nothing)

    return state


def test_a_visitor_is_asked_until_their_chat_has_a_reply(client, checks):
    """A reply is signed only after the check, so a made-up one doesn't skip it."""
    client.post("/help/chat", json={"messages": [QUESTION]})
    reply = {"role": "assistant", "content": "Paste it."}
    signed = {
        **reply,
        "signature": reply_signature("Paste it.", help_signing_key(settings.service_secret)),
    }
    client.post("/help/chat", json={"messages": [QUESTION, signed, QUESTION]})

    assert checks["asked"] == ["/help/chat"]

    client.post("/help/chat", json={"messages": [QUESTION, reply, QUESTION]})

    assert checks["asked"] == ["/help/chat", "/help/chat"]


def test_a_contact_message_is_asked_and_one_that_fails_isnt_sent(client, checks, monkeypatch):
    saved = []

    async def save(data):
        saved.append(data)

    monkeypatch.setattr(help_routes.contact_store, "save", save)
    checks["refuse"] = True
    body = {"name": "Ann", "email": "ann@example.com", "message": "Do you offer invoices?"}

    assert client.post("/help/contact", json=body).status_code == 403
    assert checks["asked"] == ["/help/contact"]
    assert saved == []
