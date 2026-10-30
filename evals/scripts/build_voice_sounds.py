"""Synthesises datasets/voice_sounds.json's sounds (coughs, knocks, thunder, music and more: no
recordings) with ffmpeg into datasets/audio/sound_<id>.ogg, Ogg Opus as browsers record, for
voice_listening_test.mjs and voice_answers_test.py. Runs on the host (the containers have no
encoder) and costs nothing; the sounds are frozen once made:

    python3 evals/scripts/build_voice_sounds.py"""

import subprocess

from common import DATASETS, load


def inputs_of(item: dict) -> list[str]:
    """ffmpeg's input: the formula, or the made-up voice message a television plays."""
    if "speech" in item:
        return ["-i", str(DATASETS / "audio" / f"{item['speech']}.ogg")]

    return ["-f", "lavfi", "-i", item["source"]]


def build(item: dict) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            *inputs_of(item),
            "-af",
            f"{item['filters']},volume={item['gain']},alimiter=limit=0.95",
            "-ac",
            "1",
            "-ar",
            "48000",
            "-c:a",
            "libopus",
            str(DATASETS / "audio" / f"sound_{item['id']}.ogg"),
        ],
        check=True,
    )


if __name__ == "__main__":
    items = load(DATASETS / "voice_sounds.json")["items"]

    for item in items:
        build(item)

    print(f"{len(items)} sounds built")
