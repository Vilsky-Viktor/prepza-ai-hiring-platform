import json

import pytest
from prepza_common.user import User

from app.auth import user_with_token
from app.main import app
from app.services import transcribe, turns

ANN = User(uid="ann", email="ann@example.com", email_verified=True)
COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
KEY = "pz_a8Kq3ZpL0vW7tYx2Rn5BdF9hJ4mC6sQe1Ug"


def events(body: str) -> list[dict]:
    return [json.loads(line[5:]) for line in body.splitlines() if line.startswith("data:")]


@pytest.fixture
def nothing_else(monkeypatch):
    """Anything a message normally goes through fails the test."""
    app.dependency_overrides[user_with_token] = lambda: (ANN, "user-token")

    def touched(*args, **kwargs):
        pytest.fail("a message with a secret went further")

    monkeypatch.setattr(turns, "refuse_if_paused", touched)
    monkeypatch.setattr(turns, "user_companies", touched)
    monkeypatch.setattr(turns.conversations, "create", touched)
    monkeypatch.setattr(turns.messages, "add_question", touched)
    monkeypatch.setattr(turns.limits, "check", touched)
    monkeypatch.setattr(turns, "build_messages", touched)

    yield

    app.dependency_overrides.clear()


def test_a_message_with_a_key_is_answered_without_being_stored_counted_or_read(
    client, nothing_else
):
    body = {"message": f"Here is my API key {KEY}", "company_id": COMPANY}
    response = client.post("/chat", json=body, headers={"Accept-Language": "de"})
    found = events(response.text)

    assert found[0] == {"removed": True}
    assert found[1]["delta"].startswith("Ich habe deine Nachricht entfernt")
    assert found[1]["delta"].endswith("Gib es selbst auf der Seite für API-Schlüssel ein.")
    assert found[2] == {
        "block": {
            "kind": "link",
            "items": [],
            "links": [f"/companies/{COMPANY}/integrations/api"],
            "page": "api",
            "label": "API-Schlüssel",
        }
    }
    assert found[-1] == {"done": {"message_id": None}}
    assert KEY not in response.text


def test_without_a_known_form_the_answer_is_general(client, nothing_else):
    response = client.post("/chat", json={"message": "AKIAIOSFODNN7EXAMPLE"})
    found = events(response.text)

    assert found[1]["delta"].endswith("Enter it yourself in the right form on the site.")
    assert not [event for event in found if "block" in event]


def test_a_secret_in_the_chat_carried_from_before_signing_in_is_caught_too(client, nothing_else):
    earlier = [{"role": "user", "content": f"my token ghp_{'a1B2c3D4' * 5}"}]
    found = events(client.post("/chat", json={"message": "Hi", "earlier": earlier}).text)

    assert found[0] == {"removed": True}


def test_a_secret_said_aloud_never_comes_back_as_text(client, monkeypatch):
    from types import SimpleNamespace

    app.dependency_overrides[user_with_token] = lambda: (ANN, "user-token")

    async def create(**arguments):
        return SimpleNamespace(text=f"my key is {KEY}", usage=None)

    async def nothing(*args, **kwargs):
        pass

    client_ = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create)))
    monkeypatch.setattr(transcribe, "get_openai", lambda: client_)
    monkeypatch.setattr(transcribe, "refuse_if_paused", nothing)
    monkeypatch.setattr(transcribe.limits, "check_transcription", nothing)
    monkeypatch.setattr(transcribe.limits, "record", nothing)
    response = client.post(
        "/transcribe", content=b"\x1a\x45\xdf\xa3opus", headers={"Content-Type": "audio/webm"}
    )
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert KEY not in response.text
    assert "contained a secret" in response.json()["detail"]


def test_the_greenhouse_secret_seen_on_localhost_is_removed_and_linked_to_integrations(
    client, nothing_else
):
    message = "Add my secret to Greenhouse ATS integration: 94uf9jf394ur0fj394g3ffh3"
    response = client.post("/chat", json={"message": message, "company_id": COMPANY})
    found = events(response.text)

    assert found[0] == {"removed": True}
    assert found[1]["delta"].endswith("Enter it yourself on the integrations page.")
    assert found[2]["block"]["links"] == [f"/companies/{COMPANY}/integrations"]
    assert found[2]["block"]["label"] == "integrations"
    assert "94uf9jf394ur0fj394g3ffh3" not in response.text
