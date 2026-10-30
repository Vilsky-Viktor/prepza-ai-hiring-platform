"""OpenAI's realtime voice model saying a text: one connection per reading, audio only, no
conversation around it."""

import asyncio
import base64

from websockets.exceptions import WebSocketException

from rounds.config import settings
from rounds.constants.voice import SPEECH_RATE, SPEECH_TIMEOUT_SECONDS
from rounds.core.exceptions import SpeechFailed
from rounds.integrations.llm import get_speech_client


async def say(instructions: str) -> tuple[bytes, str]:
    """What the model says for `instructions` (which hold the text): 16-bit mono PCM at
    SPEECH_RATE, and its own transcript of it. SpeechFailed on the model's or the connection's
    error; TimeoutError after SPEECH_TIMEOUT_SECONDS."""
    audio, transcript = bytearray(), ""
    output = {"format": {"type": "audio/pcm", "rate": SPEECH_RATE}, "voice": settings.speech_voice}

    try:
        async with (
            asyncio.timeout(SPEECH_TIMEOUT_SECONDS),
            get_speech_client().realtime.connect(model=settings.speech_model) as connection,
        ):
            await connection.session.update(
                session={
                    "type": "realtime",
                    "output_modalities": ["audio"],
                    "audio": {"output": output},
                }
            )
            await connection.response.create(response={"input": [], "instructions": instructions})

            async for event in connection:
                if event.type == "response.output_audio.delta":
                    audio += base64.b64decode(event.delta)
                elif event.type == "response.output_audio_transcript.delta":
                    transcript += event.delta
                elif event.type == "error":
                    raise SpeechFailed(event.error.message)
                elif event.type == "response.done":
                    break
    except WebSocketException as error:
        raise SpeechFailed(type(error).__name__) from error

    return bytes(audio), transcript
