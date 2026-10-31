"""OpenAI's realtime transcription: a spoken answer streamed while it's said, one session per
answer. The session is opened before the candidate speaks and the audio is sent as it comes, so
at its end nothing is left to upload and the text follows within a second. The audio and the
words stay in memory."""

import asyncio
import base64
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from openai import OpenAIError
from openai.resources.realtime.realtime import AsyncRealtimeConnection
from testee_common.ai.speech import TRANSCRIBE_LANGUAGES
from websockets.exceptions import WebSocketException

from rounds.config import settings
from rounds.constants.voice import LIVE_FINAL_TIMEOUT_SECONDS, LIVE_OPEN_TIMEOUT_SECONDS, LIVE_RATE
from rounds.integrations.llm import get_speech_client

# What a keyword may not hold (OpenAI refuses the session otherwise).
NOT_IN_KEYWORDS = str.maketrans({"<": " ", ">": " ", "\r": " ", "\n": " "})
FINAL = "conversation.item.input_audio_transcription.completed"


class HearingFailed(OpenAIError):
    """OpenAI's realtime transcription reported an error, or its connection broke."""


def session_config(language: str, keywords: list[str], model: str, delay: str | None) -> dict:
    """A transcription session's settings: PCM at LIVE_RATE, `model`, the interview's language,
    the words it's likely to hear, a delay (speed against accuracy: gpt-live-transcribe's only)
    when given, and no turn detection of its own (the browser's detector says when the answer
    ends)."""
    hints = [" ".join(word.translate(NOT_IN_KEYWORDS).split()) for word in keywords]
    transcription = {
        "model": model,
        "languages": [TRANSCRIBE_LANGUAGES.get(language, language)],
    }

    if delay:
        transcription["delay"] = delay

    if any(hints):
        transcription["keywords"] = [hint for hint in hints if hint]

    return {
        "type": "transcription",
        "audio": {
            "input": {
                "format": {"type": "audio/pcm", "rate": LIVE_RATE},
                "transcription": transcription,
                "turn_detection": None,
            }
        },
    }


async def until(connection: AsyncRealtimeConnection, wanted: str) -> dict:
    """The next event of type `wanted`, skipping others; HearingFailed on an error event."""
    async for event in connection:
        if event.type == "error":
            raise HearingFailed(event.error.type)

        if event.type == wanted:
            return event.model_dump()

    raise HearingFailed("closed")


class LiveHearing:
    """One answer's session: audio in as it's said, then its final text. OpenAI's events are read
    as they come (the text so far isn't used: only the final text is matched), so the connection
    never stalls on unread ones and an error ends the answer at once. `seconds`: the audio sent,
    as OpenAI bills it once it has given the final text (`done`)."""

    def __init__(self, connection: AsyncRealtimeConnection):
        self.connection = connection
        self.sent = 0
        self.billed: float | None = None
        self.done = False
        self.finished: asyncio.Future[dict] = asyncio.get_running_loop().create_future()
        self.reader = asyncio.create_task(self.read())

    @property
    def seconds(self) -> float:
        return self.billed or self.sent / 2 / LIVE_RATE

    async def read(self) -> None:
        """Reads OpenAI's events until the final text, an error or the connection's end."""
        try:
            self.finished.set_result(await until(self.connection, FINAL))
        except (HearingFailed, WebSocketException) as error:
            self.finished.set_exception(HearingFailed(type(error).__name__))

    def failed(self) -> None:
        """Raises the error OpenAI reported meanwhile, if any."""
        if self.finished.done() and self.finished.exception():
            raise self.finished.exception()

    async def send(self, pcm: bytes) -> None:
        """Adds 16-bit mono PCM at LIVE_RATE to the answer."""
        self.failed()

        if not pcm:
            return

        self.sent += len(pcm)

        try:
            await self.connection.send(
                {"type": "input_audio_buffer.append", "audio": base64.b64encode(pcm).decode()}
            )
        except WebSocketException as error:
            raise HearingFailed(type(error).__name__) from error

    async def final(self) -> str:
        """The answer has ended: its final text. TimeoutError after LIVE_FINAL_TIMEOUT_SECONDS."""
        self.failed()

        try:
            async with asyncio.timeout(LIVE_FINAL_TIMEOUT_SECONDS):
                await self.connection.send({"type": "input_audio_buffer.commit"})
                done = await asyncio.shield(self.finished)
        except WebSocketException as error:
            raise HearingFailed(type(error).__name__) from error

        self.billed = (done.get("usage") or {}).get("seconds")
        self.done = True

        return done.get("transcript", "").strip()

    async def close(self) -> None:
        self.reader.cancel()

        if self.finished.done() and not self.finished.cancelled():
            self.finished.exception()  # retrieved, so an unawaited failure isn't reported

        await self.connection.close()


@asynccontextmanager
async def live_hearing(
    language: str, keywords: list[str], model: str | None = None, delay: str | None = None
) -> AsyncIterator[LiveHearing]:
    """A realtime transcription session (`model`, the transcribe_model setting by default), ready
    for audio (its settings confirmed by OpenAI), closed on leaving. HearingFailed when it can't
    be opened; TimeoutError after LIVE_OPEN_TIMEOUT_SECONDS."""
    config = session_config(language, keywords, model or settings.transcribe_model, delay)

    try:
        async with asyncio.timeout(LIVE_OPEN_TIMEOUT_SECONDS):
            manager = get_speech_client().realtime.connect(extra_query={"intent": "transcription"})
            connection = await manager.enter()
    except WebSocketException as error:
        raise HearingFailed(type(error).__name__) from error

    hearing = None

    try:
        async with asyncio.timeout(LIVE_OPEN_TIMEOUT_SECONDS):
            await connection.send({"type": "session.update", "session": config})
            await until(connection, "session.updated")

        hearing = LiveHearing(connection)
        yield hearing
    except WebSocketException as error:
        raise HearingFailed(type(error).__name__) from error
    finally:
        await (hearing.close() if hearing else connection.close())
