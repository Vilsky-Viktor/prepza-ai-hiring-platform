"""Speaks datasets/voice.json's messages into datasets/audio/<id>.ogg with OpenAI's
text-to-speech (Ogg Opus, a format the assistant's microphone sends), for transcription_test.py.
The audio is frozen once made: run it again only to rebuild the set on purpose.

    evals/run.sh assistant build_audio.py

Costs about a cent."""

import asyncio

from common import DATASETS, load

from assistant.integrations.llm import get_openai

VOICE_MODEL = "gpt-4o-mini-tts"
VOICE = "alloy"


async def speak(item: dict) -> None:
    reply = await get_openai().audio.speech.create(
        model=VOICE_MODEL, voice=VOICE, input=item["text"], response_format="opus"
    )
    path = DATASETS / "audio" / f"{item['id']}.ogg"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(reply.content)


async def main() -> None:
    items = load(DATASETS / "voice.json")["items"]
    await asyncio.gather(*(speak(item) for item in items))
    print(f"{len(items)} messages spoken")


if __name__ == "__main__":
    asyncio.run(main())
