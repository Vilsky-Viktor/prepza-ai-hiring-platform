"""Speech for the evals' audio datasets, by OpenAI's realtime voice model (`gpt-realtime-2.1-mini`,
the replacement OpenAI names for its text-to-speech models): one connection per clip, the text in
the instructions ("Say exactly the following:", OpenAI's pattern for speech with no conversation
around it), 16-bit mono PCM saved as WAV, and the model's own transcript of what it said, so a
clip that strays from its text is spoken again. The container has no Opus encoder: ffmpeg on the
host turns the WAV into Ogg Opus, as browsers record."""

import base64
import wave
from pathlib import Path

VOICE_MODEL = "gpt-realtime-2.1-mini"
SAMPLE_RATE = 24000


async def say(client, voice: str, instructions: str) -> tuple[bytes, str]:
    """What the model says for `instructions` in `voice`: PCM and its transcript."""
    audio, transcript = bytearray(), ""
    output = {"format": {"type": "audio/pcm", "rate": SAMPLE_RATE}, "voice": voice}

    async with client.realtime.connect(model=VOICE_MODEL) as connection:
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
                raise RuntimeError(event.error.message)
            elif event.type == "response.done":
                break

    return bytes(audio), transcript


def save_wav(path: Path, audio: bytes) -> None:
    path.parent.mkdir(exist_ok=True)

    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(audio)
