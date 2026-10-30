"""Speaks datasets/voice_answers.json's `spoken` answers with OpenAI's realtime voice model
(realtime_speech.py; each answer with its voice and way of speaking) into
datasets/audio/answer_<id>.wav, for voice_answers_test.py. An answer whose spoken words (the
model's own transcript) stray from it is spoken again. The audio is frozen once made: run it again
only to rebuild the set on purpose. Then, on the host (the container has no encoder), each is
encoded to Ogg Opus, as browsers record, with pink noise mixed into the noisy ones:

    evals/run.sh rounds build_voice_answers.py
    python3 evals/scripts/build_voice_answers.py --encode

Costs about two cents."""

import argparse
import asyncio
import subprocess

from common import DATASETS, load
from realtime_speech import save_wav, say
from text_checks import error_rate

# Pink noise this loud under the voice: a busy room, the answer still clear to a person.
NOISE = "anoisesrc=color=pink:amplitude=0.06"
# An answer is kept when its transcript differs from it by at most this share of characters:
# answers are short, so a dropped letter must count.
MAX_ERROR_RATE = 0.1
ATTEMPTS = 4
# Sessions open at once: more time out.
MAX_CONCURRENCY = 4
INSTRUCTIONS = (
    "You are a voice actor recording a candidate's spoken answer in a job interview. {style} "
    "Say exactly the following, word for word, in its own language, and nothing else: no "
    "greeting, introduction or translation.\n\n{text}"
)


def path_of(item: dict, suffix: str):
    return DATASETS / "audio" / f"answer_{item['id']}.{suffix}"


async def speak(client, item: dict, slots: asyncio.Semaphore) -> None:
    # Here, not at the top: the encoding step runs on the host, without the package.
    from websockets.exceptions import ConnectionClosed

    spoken = item["spoken"]
    instructions = INSTRUCTIONS.format(style=spoken["style"], text=item["said"])

    for _ in range(ATTEMPTS):
        async with slots:
            try:
                audio, transcript = await say(client, spoken["voice"], instructions)
            except (RuntimeError, ConnectionClosed):
                # A dropped connection or the model's error: another attempt.
                transcript = ""
                continue

        if error_rate(item["said"], transcript) <= MAX_ERROR_RATE:
            break
    else:
        raise RuntimeError(f"{item['id']}: spoken as {transcript!r}")

    save_wav(path_of(item, "wav"), audio)


async def build(items: list[dict]) -> None:
    from rounds.integrations.llm import get_speech_client

    client = get_speech_client()
    slots = asyncio.Semaphore(MAX_CONCURRENCY)
    await asyncio.gather(*(speak(client, item, slots) for item in items))
    print(f"{len(items)} answers spoken")


def encode(items: list[dict]) -> None:
    """Each WAV as Ogg Opus, pink noise mixed in where the answer asks for it."""
    for item in items:
        wav = path_of(item, "wav")
        noise = [
            "-f",
            "lavfi",
            "-i",
            NOISE,
            "-filter_complex",
            "amix=inputs=2:duration=first:normalize=0",
        ]
        mix = noise if item["spoken"]["noise"] else []
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(wav),
                *mix,
                "-c:a",
                "libopus",
                str(path_of(item, "ogg")),
            ],
            check=True,
        )
        wav.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--encode", action="store_true")
    args = parser.parse_args()
    spoken = [i for i in load(DATASETS / "voice_answers.json")["items"] if "spoken" in i]

    if args.encode:
        encode(spoken)
    else:
        asyncio.run(build(spoken))
