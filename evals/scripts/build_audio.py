"""Speaks datasets/voice.json's messages with OpenAI's realtime speech model (`gpt-realtime-2.1-mini`,
the replacement OpenAI names for its text-to-speech models) into datasets/audio/<id>.wav, for
transcription_test.py. A clip whose spoken words (the model's own transcript) stray from the text
is spoken again. The audio is frozen once made: run it again only to rebuild the set on purpose.

    evals/run.sh assistant build_audio.py
    for f in evals/datasets/audio/*.wav; do
      ffmpeg -loglevel error -y -i "$f" -c:a libopus "${f%.wav}.ogg" && rm "$f"
    done

The second step encodes Ogg Opus, as browsers record (the container has no encoder). Costs a few
cents."""

import asyncio
import base64
import wave

from common import DATASETS, load
from text_checks import error_rate

from assistant.integrations.llm import get_openai

VOICE_MODEL = "gpt-realtime-2.1-mini"
VOICE = "marin"
SAMPLE_RATE = 24000
# A clip is kept when its transcript differs from the text by at most this share of characters.
MAX_ERROR_RATE = 0.05
ATTEMPTS = 3
# Sessions open at once: more time out.
MAX_CONCURRENCY = 4
# OpenAI's pattern for speech with no conversation around it ("Say exactly the following:").
INSTRUCTIONS = (
    "You are a voice actor recording sample voice messages. Say exactly the following, word for "
    "word, in its own language, in a natural, clear voice, and nothing else: no greeting, "
    "introduction, answer or translation.\n\n{text}"
)


async def say(text: str) -> tuple[bytes, str]:
    """The text spoken once: 16-bit mono PCM and the model's transcript of all it said."""
    audio, transcript = bytearray(), ""

    async with get_openai().realtime.connect(model=VOICE_MODEL) as connection:
        await connection.session.update(
            session={
                "type": "realtime",
                "output_modalities": ["audio"],
                "audio": {
                    "output": {"format": {"type": "audio/pcm", "rate": SAMPLE_RATE}, "voice": VOICE}
                },
            }
        )
        await connection.response.create(
            response={"input": [], "instructions": INSTRUCTIONS.format(text=text)}
        )

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


async def speak(item: dict, slots: asyncio.Semaphore) -> None:
    for _ in range(ATTEMPTS):
        async with slots:
            audio, transcript = await say(item["text"])

        if error_rate(item["text"], transcript) <= MAX_ERROR_RATE:
            break
    else:
        raise RuntimeError(f"{item['id']}: spoken as {transcript!r}")

    path = DATASETS / "audio" / f"{item['id']}.wav"
    path.parent.mkdir(exist_ok=True)

    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(audio)


async def main() -> None:
    items = load(DATASETS / "voice.json")["items"]
    slots = asyncio.Semaphore(MAX_CONCURRENCY)
    await asyncio.gather(*(speak(item, slots) for item in items))
    print(f"{len(items)} messages spoken")


if __name__ == "__main__":
    asyncio.run(main())
