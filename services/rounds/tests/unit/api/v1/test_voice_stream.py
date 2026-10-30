# Voice mode's live listening: a spoken answer streamed over a WebSocket while it's said
# (services/voice_stream.py), OpenAI's realtime transcription faked. test_voice.py has the upload.
import asyncio
import logging
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from rounds.constants.voice import IN_TIME_KEY
from rounds.integrations.live_hearing import HearingFailed
from rounds.services import voice_stream
from tests.unit.api.v1 import test_voice

section = test_voice.section
voice = test_voice.voice
CANDIDATE = test_voice.CANDIDATE
# One frame of the browser's speech detector: 512 samples of 16-bit PCM at 16 kHz.
FRAME = bytes(1024)


class FakeHearing:
    """OpenAI's transcription session: the audio it got, and its final text."""

    def __init__(self, text: str, fails: Exception | None = None):
        self.text = text
        self.fails = fails
        self.audio = bytearray()
        self.sent = 0
        self.done = False
        self.billed = None

    @property
    def seconds(self):
        return self.billed or self.sent / 2 / 24_000

    async def send(self, pcm: bytes):
        self.audio += pcm
        self.sent += len(pcm)

    async def final(self):
        if self.fails:
            raise self.fails

        self.done = True
        self.billed = 1.5

        return self.text


@pytest.fixture
def live(voice, monkeypatch):
    """The candidate signs in with the token "good"; each session OpenAI opens is kept, with its
    language and keywords. `opening` fails the opening when set."""
    state = SimpleNamespace(sessions=[], opening=None, fails=None)

    def verify(token, check_revoked=False):
        assert check_revoked

        return CANDIDATE if token == "good" else None

    @asynccontextmanager
    async def live_hearing(language, keywords, model=None, delay=None):
        if state.opening:
            raise state.opening

        hearing = FakeHearing(voice.heard, state.fails)
        state.sessions.append(
            SimpleNamespace(language=language, keywords=keywords, hearing=hearing)
        )

        yield hearing

    monkeypatch.setattr(voice_stream, "verify", verify)
    monkeypatch.setattr(voice_stream, "live_hearing", live_hearing)

    return state


def url(voice) -> str:
    return f"/sessions/{voice.row.id}/voice/stream"


def close_code(socket) -> int:
    """The code the service closed with, skipping any message before it."""
    while True:
        message = socket.receive()

        if message["type"] == "websocket.close":
            return message["code"]


def signed_in(socket, token="good"):
    socket.send_json({"token": token})

    return socket.receive_json()


def test_an_answer_streamed_while_spoken_is_heard_and_matched(
    client, voice, live, published, redis
):
    with client.websocket_connect(url(voice)) as socket:
        assert signed_in(socket) == {"type": "ready"}
        socket.send_json({"type": "start"})

        for _ in range(10):
            socket.send_bytes(FRAME)

        socket.send_json({"type": "end", "waiting": [2, 2]})
        reply = socket.receive_json()
        code = close_code(socket)

    assert code == 1000
    assert reply["type"] == "answer"
    # One option on a single-answer question: clear, saved without asking.
    assert reply["answer"] == {
        "heard": "die Mediane",
        "intent": "choose",
        "picks": [1],
        "clear": True,
    }
    assert list(reply["stages"]) == ["transcribe", "match", "total"]
    [opened] = live.sessions
    # Heard in the interview's language, told the options' letters and texts.
    assert opened.language == "de"
    assert opened.keywords == ["A", "B", "C", "D", "Mean", "Median", "Range", "Mode"]
    # The browser's 16 kHz audio reaches OpenAI at 24 kHz: half as many bytes again.
    assert len(opened.hearing.audio) == 15 * 1024
    [(_question, said, waiting, language)] = voice.matched
    assert (said, waiting, language) == ("die Mediane", [2], "de")
    used = [data for kind, data in published if kind == "ai.used"]
    assert [(u["action"], u["model"], u["outcome"]) for u in used] == [
        ("voice_transcription", "gpt-transcribe", "ok"),
        ("voice_match", "gpt-6-luna", "ok"),
    ]
    # The seconds OpenAI billed.
    assert used[0]["audio_seconds"] == 1.5
    # Counted as one answer and one connection; its arrival noted for the time-up grace.
    assert redis.counts[f"rate:voice:answers:user:{CANDIDATE.uid}"] == 1
    assert redis.counts[f"rate:voice:streams:user:{CANDIDATE.uid}"] == 1
    assert redis.counts[IN_TIME_KEY.format(session_id=voice.row.id)] == voice.row.questions[0]["id"]


@pytest.mark.parametrize(
    ("row", "token", "code"),
    [
        (section(), "stale", 4401),
        (section(user_id="someone-else"), "good", 4404),
        (section(voice=False), "good", 4409),
        (section(shown=False), "good", 4409),
    ],
)
def test_only_the_candidates_own_voice_question_on_the_clock_is_streamed(
    client, voice, live, row, token, code
):
    voice.row = row

    with client.websocket_connect(url(voice)) as socket:
        socket.send_json({"token": token})

        assert close_code(socket) == code

    assert live.sessions == []


@pytest.mark.parametrize(
    "steps",
    [
        # Audio before the answer is counted.
        [FRAME],
        # A frame larger than any the detector makes.
        [{"type": "start"}, bytes(16_386)],
        # Half a sample.
        [{"type": "start"}, b"\x00"],
        [{"type": "end"}],
        [{"type": "start"}, {"type": "start"}],
        [{"type": "listen"}],
        [{"type": "end", "waiting": [4]}],
    ],
)
def test_anything_out_of_turn_closes_the_stream(client, voice, live, published, steps):
    with client.websocket_connect(url(voice)) as socket:
        signed_in(socket)

        for step in steps:
            if isinstance(step, bytes):
                socket.send_bytes(step)
            else:
                socket.send_json(step)

        assert close_code(socket) == 4400

    assert voice.matched == []


def test_an_answer_longer_than_allowed_closes_the_stream(client, voice, live, monkeypatch):
    monkeypatch.setattr(voice_stream, "MAX_ANSWER_SECONDS", 0.05)

    with client.websocket_connect(url(voice)) as socket:
        signed_in(socket)
        socket.send_json({"type": "start"})
        socket.send_bytes(FRAME)
        socket.send_bytes(FRAME)

        assert close_code(socket) == 4400


@pytest.mark.parametrize("limit", ["VOICE_ANSWERS_PER_USER_HOUR", "VOICE_STREAMS_PER_USER_HOUR"])
def test_streams_stop_at_the_candidates_limits(client, voice, live, redis, limit):
    redis.limits[limit] = 1

    with client.websocket_connect(url(voice)) as socket:
        signed_in(socket)
        socket.send_json({"type": "start"})
        socket.send_json({"type": "end"})
        socket.receive_json()

    with client.websocket_connect(url(voice)) as socket:
        socket.send_json({"token": "good"})

        if limit == "VOICE_ANSWERS_PER_USER_HOUR":
            assert socket.receive_json() == {"type": "ready"}
            socket.send_json({"type": "start"})

        assert close_code(socket) == 4429


@pytest.mark.parametrize(
    ("opening", "fails", "code"),
    [
        (HearingFailed("closed"), None, 4502),
        (TimeoutError(), None, 4504),
        (None, HearingFailed("server_error"), 4502),
        (None, TimeoutError(), 4504),
    ],
)
def test_openais_failures_close_the_stream_and_the_audio_sent_is_paid_for(
    client, voice, live, published, opening, fails, code
):
    live.opening, live.fails = opening, fails

    with client.websocket_connect(url(voice)) as socket:
        socket.send_json({"token": "good"})

        if opening is None:
            assert socket.receive_json() == {"type": "ready"}
            socket.send_json({"type": "start"})
            socket.send_bytes(FRAME)
            socket.send_json({"type": "end"})

        assert close_code(socket) == code

    used = [(data["action"], data["outcome"]) for kind, data in published if kind == "ai.used"]
    assert used == ([] if opening else [("voice_transcription", "failed")])


def test_a_browser_gone_mid_answer_pays_for_the_audio_sent(client, voice, live, published):
    with client.websocket_connect(url(voice)) as socket:
        signed_in(socket)
        socket.send_json({"type": "start"})
        socket.send_bytes(FRAME)

    used = [(data["action"], data["outcome"]) for kind, data in published if kind == "ai.used"]
    assert used == [("voice_transcription", "failed")]
    assert voice.matched == []


def test_an_instance_with_its_streams_full_sends_the_candidate_to_the_upload(
    client, voice, live, monkeypatch
):
    monkeypatch.setattr(voice_stream, "stream_slots", asyncio.Semaphore(0))

    with client.websocket_connect(url(voice)) as socket:
        assert close_code(socket) == 4503

    assert live.sessions == []


def test_the_candidates_words_and_token_reach_no_log(client, voice, live, caplog):
    caplog.set_level(logging.DEBUG)

    with client.websocket_connect(url(voice)) as socket:
        signed_in(socket)
        socket.send_json({"type": "start"})
        socket.send_bytes(FRAME)
        socket.send_json({"type": "end"})
        socket.receive_json()

    assert "Voice answer" in caplog.text
    assert "die Mediane" not in caplog.text
    assert "good" not in caplog.text
