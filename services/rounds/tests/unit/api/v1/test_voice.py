from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.i18n.i18n import translate

from rounds.constants.voice_phrases import GOT_IT, NEXT, TIME_UP
from rounds.integrations import library
from rounds.main import app
from rounds.models.sessions import Session
from rounds.schemas.voice import VoiceMatch
from rounds.services import session_access, voice_answers, voice_match, voice_session

CANDIDATE = User(uid="cand", email="cand@example.com", email_verified=True)
OGG = {"Content-Type": "audio/ogg"}
SPOKEN = b"OggS spoken answer"


def section(voice=True, shown=True, user_id="cand") -> Session:
    return Session(
        id=uuid4(),
        user_id=user_id,
        topic_id=uuid4(),
        interview_set_id=uuid4(),
        candidate_invite_id=uuid4(),
        company_id=uuid4(),
        topic_title="Statistics",
        status="in_progress",
        questions=[
            {
                "id": str(uuid4()),
                "text": "Which measure ignores outliers best?",
                "options": [
                    {"answer": "Mean", "correct": False},
                    {"answer": "Median", "correct": True},
                    {"answer": "Range", "correct": False},
                    {"answer": "Mode", "correct": False},
                ],
                "seconds": 60,
            }
        ],
        question_seconds=60,
        question_shown_at=datetime.now(UTC) if shown else None,
        voice=voice,
        preview=False,
        answers=[],
    )


@pytest.fixture
def voice(monkeypatch):
    """A candidate's voice interview in German, OpenAI's hearing and matching faked: what each
    got, and the row a test can change."""
    state = SimpleNamespace(row=section(), heard="die Mediane", heard_calls=[], matched=[])

    async def read(session_id):
        return state.row if session_id == state.row.id else None

    async def german_set(set_id):
        return {"title": "Statistik", "language": "de"}

    async def create(**arguments):
        state.heard_calls.append(arguments)

        return SimpleNamespace(text=state.heard, usage=SimpleNamespace(seconds=2.0))

    async def read_match(question, said, waiting, language):
        state.matched.append((question, said, waiting, language))

        return VoiceMatch(intent="choose", letters=["B"]), {"input_tokens": 300}

    hearing = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create)))
    monkeypatch.setattr(session_access, "read", read)
    monkeypatch.setattr(library, "get_set", german_set)
    monkeypatch.setattr(voice_answers, "get_transcribe_client", lambda: hearing)
    monkeypatch.setattr(voice_match, "read_match", read_match)
    app.dependency_overrides[current_user] = lambda: CANDIDATE

    return state


def test_a_spoken_answer_is_heard_in_the_interviews_language_and_matched(client, voice, published):
    response = client.post(
        f"/sessions/{voice.row.id}/voice/answers?waiting=2", content=SPOKEN, headers=OGG
    )

    assert response.status_code == 200
    assert response.json() == {"heard": "die Mediane", "intent": "choose", "picks": [1]}
    [heard] = voice.heard_calls
    assert heard["file"] == ("audio.ogg", SPOKEN, "audio/ogg")
    assert heard["languages"] == ["de"]
    [(question, said, waiting, language)] = voice.matched
    # The matching never sees which option is right.
    assert question.options == ["Mean", "Median", "Range", "Mode"]
    assert (said, waiting, language) == ("die Mediane", [2], "de")
    used = [data for kind, data in published if kind == "ai.used"]
    assert [(u["action"], u["company_id"]) for u in used] == [
        ("voice_transcription", str(voice.row.company_id)),
        ("voice_match", str(voice.row.company_id)),
    ]
    assert used[0]["audio_seconds"] == 2.0


def test_silence_is_unclear_without_a_matching_call(client, voice):
    voice.heard = "  "

    response = client.post(f"/sessions/{voice.row.id}/voice/answers", content=SPOKEN, headers=OGG)

    assert response.json() == {"heard": "", "intent": "unclear", "picks": []}
    assert voice.matched == []


@pytest.mark.parametrize(
    ("row", "status"),
    [
        (section(voice=False), 409),
        (section(shown=False), 409),
        (section(user_id="someone-else"), 404),
    ],
)
def test_only_the_candidates_own_voice_question_on_the_clock_is_heard(client, voice, row, status):
    voice.row = row

    response = client.post(f"/sessions/{row.id}/voice/answers", content=SPOKEN, headers=OGG)

    assert response.status_code == status
    assert voice.heard_calls == []


def test_a_body_that_isnt_a_recording_is_refused(client, voice):
    response = client.post(
        f"/sessions/{voice.row.id}/voice/answers", content=b"<html>", headers=OGG
    )

    assert response.status_code == 415
    assert voice.heard_calls == []


def test_spoken_answers_stop_at_the_candidates_hourly_limit(client, voice, redis):
    redis.limits["VOICE_ANSWERS_PER_USER_HOUR"] = 1
    url = f"/sessions/{voice.row.id}/voice/answers"

    assert client.post(url, content=SPOKEN, headers=OGG).status_code == 200

    refused = client.post(url, content=SPOKEN, headers=OGG)

    assert refused.status_code == 429
    assert len(voice.heard_calls) == 1


def test_the_question_is_played_only_once_its_clock_started(client, voice, monkeypatch):
    read_aloud = []

    async def clip_for(row, text, language, company_text):
        read_aloud.append((text, language, company_text))

        return SimpleNamespace(audio=b"OggS question", seconds=4.0)

    monkeypatch.setattr(voice_session, "clip_for", clip_for)
    url = f"/sessions/{voice.row.id}/voice/question"

    played = client.get(url)

    assert played.status_code == 200
    assert played.headers["content-type"] == "audio/ogg"
    assert played.content == b"OggS question"
    assert read_aloud == [
        (
            "Which measure ignores outliers best? A: Mean. B: Median. C: Range. D: Mode.",
            "de",
            True,
        )
    ]

    voice.row = section(shown=False)

    assert client.get(f"/sessions/{voice.row.id}/voice/question").status_code == 409


def test_a_confirmation_names_the_options_and_needs_some(client, voice, monkeypatch):
    read_aloud = []

    async def clip_for(row, text, language, company_text):
        read_aloud.append((text, company_text))

        return SimpleNamespace(audio=b"OggS", seconds=1.0)

    monkeypatch.setattr(voice_session, "clip_for", clip_for)
    base = f"/sessions/{voice.row.id}/voice"

    assert client.get(f"{base}/confirmations?picks=2&picks=0").status_code == 200
    assert client.get(f"{base}/confirmations").status_code == 422
    assert client.get(f"{base}/confirmations?picks=4").status_code == 422
    assert client.get(f"{base}/phrases/end").status_code == 200
    assert client.get(f"{base}/phrases/got-it").status_code == 200
    assert client.get(f"{base}/phrases/next").status_code == 200
    assert client.get(f"{base}/phrases/time-up").status_code == 200
    assert client.get(f"{base}/phrases/anything").status_code == 422
    # Mira no longer reminds a silent candidate: she just listens.
    assert client.get(f"{base}/phrases/reminder").status_code == 422
    assert [company for _, company in read_aloud] == [False] * 5
    # In the interview's language.
    assert [text for text, _ in read_aloud[-3:]] == [
        translate(phrase, "de") for phrase in (GOT_IT, NEXT, TIME_UP)
    ]


def test_the_candidates_words_reach_no_log_trace_or_event(
    client, voice, published, monkeypatch, caplog
):
    """The spoken answer's text goes back to the candidate only: the trace keeps the reading
    (intent and letters), the usage events their counts, and no log line quotes it."""
    traced = []
    monkeypatch.setattr(voice_match, "traced_call", lambda *arguments: traced.append(arguments))
    caplog.set_level("DEBUG")

    response = client.post(f"/sessions/{voice.row.id}/voice/answers", content=SPOKEN, headers=OGG)

    assert response.json()["heard"] == "die Mediane"
    [arguments] = traced
    assert arguments[-1] == {"intent": "choose", "letters": ["B"]}
    assert "Mediane" not in repr(arguments)
    assert "Mediane" not in repr(published)
    assert "Mediane" not in caplog.text


def test_a_plain_yes_confirms_without_a_matching_call(client, voice, published):
    voice.heard = "Ja, genau."

    response = client.post(
        f"/sessions/{voice.row.id}/voice/answers?waiting=1", content=SPOKEN, headers=OGG
    )

    assert response.json() == {"heard": "Ja, genau.", "intent": "confirm", "picks": [1]}
    assert voice.matched == []
    # Only the hearing is paid for.
    assert [d["action"] for kind, d in published if kind == "ai.used"] == ["voice_transcription"]
