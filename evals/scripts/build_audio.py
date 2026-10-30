"""Speaks datasets/voice.json's messages with OpenAI's realtime voice model (realtime_speech.py)
into datasets/audio/<id>.wav, for transcription_test.py. A clip whose spoken words (the model's
own transcript) stray from the text is spoken again. The audio is frozen once made: run it again only to rebuild the set on purpose.

    evals/run.sh assistant build_audio.py
    for f in evals/datasets/audio/*.wav; do
      ffmpeg -loglevel error -y -i "$f" -c:a libopus "${f%.wav}.ogg" && rm "$f"
    done

The second step encodes Ogg Opus, as browsers record (the container has no encoder). Costs a few
cents."""

import asyncio

from common import DATASETS, load
from realtime_speech import save_wav, say
from text_checks import error_rate

from assistant.integrations.llm import get_openai

VOICE = "marin"
# A clip is kept when its transcript differs from the text by at most this share of characters.
MAX_ERROR_RATE = 0.05
ATTEMPTS = 3
# Sessions open at once: more time out.
MAX_CONCURRENCY = 4
INSTRUCTIONS = (
    "You are a voice actor recording sample voice messages. Say exactly the following, word for "
    "word, in its own language, in a natural, clear voice, and nothing else: no greeting, "
    "introduction, answer or translation.\n\n{text}"
)


async def speak(item: dict, slots: asyncio.Semaphore) -> None:
    for _ in range(ATTEMPTS):
        async with slots:
            audio, transcript = await say(
                get_openai(), VOICE, INSTRUCTIONS.format(text=item["text"])
            )

        if error_rate(item["text"], transcript) <= MAX_ERROR_RATE:
            break
    else:
        raise RuntimeError(f"{item['id']}: spoken as {transcript!r}")

    save_wav(DATASETS / "audio" / f"{item['id']}.wav", audio)


async def main() -> None:
    items = load(DATASETS / "voice.json")["items"]
    slots = asyncio.Semaphore(MAX_CONCURRENCY)
    await asyncio.gather(*(speak(item, slots) for item in items))
    print(f"{len(items)} messages spoken")


if __name__ == "__main__":
    asyncio.run(main())
