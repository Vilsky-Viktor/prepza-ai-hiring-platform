# OpenAI's realtime transcription session (integrations/live_hearing.py), its connection faked.
import asyncio
import base64
from types import SimpleNamespace

import pytest

from rounds.integrations import live_hearing as module
from rounds.integrations.live_hearing import HearingFailed, live_hearing, session_config

FINAL = "conversation.item.input_audio_transcription.completed"


def event(kind: str, **data):
    payload = {"type": kind, **data}

    return SimpleNamespace(
        type=kind,
        error=SimpleNamespace(type=data.get("code", "")),
        model_dump=lambda: payload,
    )


class FakeConnection:
    """OpenAI's side: confirms the settings (or refuses them), keeps the audio and answers a
    commit with `transcript` and `usage`; `then` holds events it sends of its own."""

    def __init__(self, refuse=False, transcript="B.", usage=None):
        self.refuse = refuse
        self.transcript = transcript
        self.usage = usage
        self.sent = []
        self.events = asyncio.Queue()
        self.closed = False

    async def send(self, message):
        self.sent.append(message)

        if message["type"] == "session.update":
            await self.events.put(event("error" if self.refuse else "session.updated"))
        elif message["type"] == "input_audio_buffer.commit":
            await self.events.put(event("conversation.item.input_audio_transcription.delta"))
            await self.events.put(event(FINAL, transcript=self.transcript, usage=self.usage))

    def __aiter__(self):
        return self

    async def __anext__(self):
        found = await self.events.get()

        if found is None:
            raise StopAsyncIteration

        return found

    async def close(self):
        self.closed = True


@pytest.fixture
def openai(monkeypatch):
    """The connection the session opens, and the query it opened it with."""
    state = SimpleNamespace(connection=FakeConnection(), query=None)

    def connect(extra_query):
        state.query = extra_query

        async def enter():
            return state.connection

        return SimpleNamespace(enter=enter)

    client = SimpleNamespace(realtime=SimpleNamespace(connect=connect))
    monkeypatch.setattr(module, "get_speech_client", lambda: client)

    return state


def test_a_session_is_told_the_language_the_words_and_no_turn_detection():
    config = session_config("fil", ["A", "a <b>\nc", " \r "], "gpt-transcribe", None)

    assert config == {
        "type": "transcription",
        "audio": {
            "input": {
                "format": {"type": "audio/pcm", "rate": 24_000},
                # OpenAI knows Filipino as "tl"; a keyword can't hold <, > or a line break.
                "transcription": {
                    "model": "gpt-transcribe",
                    "languages": ["tl"],
                    "keywords": ["A", "a b c"],
                },
                "turn_detection": None,
            }
        },
    }


def test_only_a_given_delay_is_sent():
    transcription = session_config("en", [], "gpt-live-transcribe", "low")["audio"]["input"][
        "transcription"
    ]

    assert transcription == {"model": "gpt-live-transcribe", "languages": ["en"], "delay": "low"}


def test_an_answer_streamed_gives_its_final_text_and_billed_seconds(openai):
    openai.connection.usage = {"type": "duration", "seconds": 2.0}

    async def scenario():
        async with live_hearing("en", ["A"]) as hearing:
            await hearing.send(b"\x01\x02" * 10)
            await hearing.send(b"")
            text = await hearing.final()

        return hearing, text

    hearing, text = asyncio.run(scenario())

    assert openai.query == {"intent": "transcription"}
    assert text == "B."
    assert (hearing.done, hearing.seconds) == (True, 2.0)
    [update, append, commit] = openai.connection.sent
    assert update["session"]["audio"]["input"]["transcription"]["model"] == "gpt-transcribe"
    assert base64.b64decode(append["audio"]) == b"\x01\x02" * 10
    assert commit == {"type": "input_audio_buffer.commit"}
    assert openai.connection.closed


def test_without_reported_usage_the_seconds_sent_are_billed(openai):
    async def scenario():
        async with live_hearing("en", []) as hearing:
            await hearing.send(bytes(48_000))
            await hearing.final()

        return hearing

    assert asyncio.run(scenario()).seconds == 1.0


def test_settings_openai_refuses_fail_the_opening_and_close_the_connection(openai):
    openai.connection.refuse = True

    async def scenario():
        async with live_hearing("en", []):
            pass

    with pytest.raises(HearingFailed):
        asyncio.run(scenario())

    assert openai.connection.closed


def test_an_error_while_audio_streams_ends_the_answer_at_once(openai):
    async def scenario():
        async with live_hearing("en", []) as hearing:
            await openai.connection.events.put(event("error", code="server_error"))
            await asyncio.sleep(0)
            await hearing.send(b"\x00\x00")

    with pytest.raises(HearingFailed):
        asyncio.run(scenario())


def test_a_connection_closed_before_the_final_text_fails_the_answer(openai):
    async def scenario():
        async with live_hearing("en", []) as hearing:
            await openai.connection.events.put(None)
            await asyncio.sleep(0)
            await hearing.final()

    with pytest.raises(HearingFailed):
        asyncio.run(scenario())
