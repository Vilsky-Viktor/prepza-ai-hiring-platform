from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from openai import APIConnectionError, RateLimitError
from testee_common.ai.speech import MAX_AUDIO_BYTES
from testee_common.auth.user import User

from assistant.api.dependencies import user_with_token
from assistant.main import app
from assistant.services import transcribe

ANN = User(uid="ann", email="ann@example.com", email_verified=True)
WEBM = {"Content-Type": "audio/webm;codecs=opus"}
# A recording as browsers make it starts with its container's signature.
OPUS = b"\x1a\x45\xdf\xa3opus"
AAC = b"\x00\x00\x00\x18ftypM4A aac"


@pytest.fixture
def openai(monkeypatch):
    """OpenAI's speech to text, answering `answer.text`; the calls it got."""
    calls = []
    answer = SimpleNamespace(text="Who passed?", usage=SimpleNamespace(seconds=4.0))

    async def create(**arguments):
        calls.append(arguments)

        if isinstance(answer.text, Exception):
            raise answer.text

        return answer

    async def not_paused(redis, what, company_id=None, user_id=None):
        pass

    async def check_transcription(redis, user_id, company_ids):
        pass

    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create)))
    monkeypatch.setattr(transcribe, "get_openai", lambda: client)
    monkeypatch.setattr(transcribe, "refuse_if_paused", not_paused)
    monkeypatch.setattr(transcribe.limits, "check_transcription", check_transcription)
    app.dependency_overrides[user_with_token] = lambda: (ANN, "user-token")

    yield SimpleNamespace(calls=calls, answer=answer)

    app.dependency_overrides.clear()


def test_a_recording_is_heard_in_the_interface_language(client, openai):
    response = client.post("/transcribe", content=OPUS, headers={**WEBM, "Accept-Language": "de"})

    assert response.json() == {"text": "Who passed?"}
    [call] = openai.calls
    assert call["file"] == ("audio.webm", OPUS, "audio/webm")
    assert call["languages"] == ["de"]
    assert call["model"] == "gpt-transcribe"


def test_filipino_is_heard_as_tagalog(client, openai):
    headers = {"Content-Type": "audio/mp4", "Accept-Language": "fil"}
    client.post("/transcribe", content=AAC, headers=headers)

    assert openai.calls[0]["languages"] == ["tl"]
    assert openai.calls[0]["file"][0] == "audio.mp4"


@pytest.mark.parametrize("body", [b"<html>not audio", b"OggS but said webm"])
def test_a_body_that_isnt_the_recording_its_type_claims_is_refused_before_openai(
    client, openai, body
):
    response = client.post("/transcribe", content=body, headers=WEBM)

    assert response.status_code == 415
    assert openai.calls == []


def test_another_format_or_a_larger_recording_is_refused_before_openai(client, openai):
    response = client.post("/transcribe", content=b"x", headers={"Content-Type": "audio/wav"})
    assert response.status_code == 415

    large = b"x" * (MAX_AUDIO_BYTES + 1)
    response = client.post("/transcribe", content=large, headers=WEBM)
    assert response.status_code == 413

    response = client.post("/transcribe", content=b"", headers=WEBM)
    assert response.status_code == 422
    assert openai.calls == []


@pytest.mark.parametrize("text", ["", "  "])
def test_nothing_heard_is_a_422_in_the_users_language(client, openai, text):
    openai.answer.text = text
    response = client.post("/transcribe", content=OPUS, headers={**WEBM, "Accept-Language": "de"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Es war nichts zu hören. Versuche es erneut."


def test_openai_failing_is_a_502_and_nothing_is_logged_of_the_recording(client, openai, caplog):
    openai.answer.text = APIConnectionError(request=httpx.Request("POST", "https://api.openai.com"))
    response = client.post("/transcribe", content=OPUS + b"secret-audio", headers=WEBM)

    assert response.status_code == 502
    assert "secret-audio" not in caplog.text


def test_a_transcription_is_recorded_with_its_audio_seconds(client, openai, published):
    openai.answer.usage = SimpleNamespace(type="duration", seconds=7.5)
    client.post("/transcribe", content=OPUS, headers=WEBM)

    [(kind, data)] = published
    assert kind == "ai.used"
    assert (data["action"], data["model"], data["audio_seconds"]) == (
        "transcription",
        "gpt-transcribe",
        7.5,
    )
    assert (data["user_id"], data["company_id"], data["outcome"]) == ("ann", None, "ok")
    assert data["cost_usd"] > 0


def test_openai_out_of_money_is_recorded_as_its_limit_and_the_call_as_failed(
    client, openai, published
):
    request = httpx.Request("POST", "https://api.openai.com")
    openai.answer.text = RateLimitError(
        "quota",
        response=httpx.Response(429, request=request),
        body={"code": "insufficient_quota"},
    )
    response = client.post("/transcribe", content=OPUS, headers=WEBM)

    assert response.status_code == 502
    hits = [data for kind, data in published if kind == "limit.hit"]
    assert [(hit["limit"], hit["kind"], hit["what"], hit["user_id"]) for hit in hits] == [
        ("OPENAI_QUOTA", "provider:openai", "transcription", "ann")
    ]
    [used] = [data for kind, data in published if kind == "ai.used"]
    assert (used["action"], used["outcome"], used["user_id"]) == ("transcription", "failed", "ann")
    assert used["audio_seconds"] > 0


def test_paused_or_over_a_limit_is_refused_before_openai(client, openai, monkeypatch):
    async def over(redis, user_id, company_ids):
        raise HTTPException(429, "over")

    monkeypatch.setattr(transcribe.limits, "check_transcription", over)
    assert client.post("/transcribe", content=OPUS, headers=WEBM).status_code == 429

    async def paused(redis, what, company_id=None, user_id=None):
        raise HTTPException(503, "paused")

    monkeypatch.setattr(transcribe, "refuse_if_paused", paused)
    assert client.post("/transcribe", content=OPUS, headers=WEBM).status_code == 503
    assert openai.calls == []


def test_signed_out_is_refused(client):
    assert client.post("/transcribe", content=OPUS, headers=WEBM).status_code in (401, 403)
