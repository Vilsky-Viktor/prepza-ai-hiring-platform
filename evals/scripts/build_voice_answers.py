"""Speaks datasets/voice_answers.json's `spoken` answers with OpenAI's text-to-speech (each with
its voice and way of speaking) into datasets/audio/answer_<id>.ogg (Ogg Opus), for
voice_answers_test.py. The audio is frozen once made: run it again only to rebuild the set on
purpose. Then the noisy ones get pink noise mixed in, on the host (the container has no ffmpeg):

    evals/run.sh rounds build_voice_answers.py
    python3 evals/scripts/build_voice_answers.py --noise

Costs under a cent."""

import argparse
import asyncio
import subprocess

from common import DATASETS, load

SPEECH_MODEL = "gpt-4o-mini-tts"
# Pink noise this loud under the voice: a busy room, the answer still clear to a person.
NOISE = "anoisesrc=color=pink:amplitude=0.06"


def path_of(item: dict):
    return DATASETS / "audio" / f"answer_{item['id']}.ogg"


async def speak(client, item: dict) -> None:
    spoken = item["spoken"]
    result = await client.audio.speech.create(
        model=SPEECH_MODEL,
        voice=spoken["voice"],
        input=item["said"],
        instructions=spoken["style"],
        response_format="opus",
    )
    path_of(item).write_bytes(result.content)


async def build(items: list[dict]) -> None:
    from rounds.integrations.llm import get_speech_client

    client = get_speech_client()
    await asyncio.gather(*(speak(client, item) for item in items))
    print(f"{len(items)} answers spoken")


def add_noise(items: list[dict]) -> None:
    for item in items:
        if not item["spoken"]["noise"]:
            continue

        path = path_of(item)
        noisy = path.with_suffix(".noisy.ogg")
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(path),
                "-f",
                "lavfi",
                "-i",
                NOISE,
                "-filter_complex",
                "amix=inputs=2:duration=first:normalize=0",
                "-c:a",
                "libopus",
                str(noisy),
            ],
            check=True,
        )
        noisy.replace(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise", action="store_true")
    args = parser.parse_args()
    spoken = [i for i in load(DATASETS / "voice_answers.json")["items"] if "spoken" in i]

    if args.noise:
        add_noise(spoken)
    else:
        asyncio.run(build(spoken))
