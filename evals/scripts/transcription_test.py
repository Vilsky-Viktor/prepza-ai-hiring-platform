"""Tests the assistant's speech to text (the microphone's voice messages) on datasets/voice.json
and its audio (build_audio.py): each recording is sent through the service's own call (its model,
the interface's language, Ogg Opus), and the text graded by code: the character error rate against
what was said (case and punctuation aside) and the language's script.

    evals/run.sh assistant transcription_test.py --label base     # --repeat 2

Costs about a cent."""

import argparse
import asyncio
import json
import time

from common import DATASETS, RESULTS, load, run_record, save
from stats import mean, share
from testee_common.ai.llm import audio_cost
from testee_common.ai.speech import audio_seconds
from text_checks import error_rate, in_script

from assistant.config import settings
from assistant.constants.limits import MAX_AUDIO_SECONDS
from assistant.services.transcribe import speech_to_text

# A message is heard right when at most this share of its characters is wrong.
MAX_ERROR_RATE = 0.1


async def hear(item: dict) -> dict:
    audio = (DATASETS / "audio" / f"{item['id']}.ogg").read_bytes()
    started = time.monotonic()
    result = await speech_to_text("audio.ogg", audio, "audio/ogg", item["language"])
    seconds = audio_seconds(getattr(result, "usage", None), len(audio), MAX_AUDIO_SECONDS)
    rate = min(error_rate(said, result.text) for said in [item["text"], *item.get("also", [])])

    return {
        "id": item["id"],
        "heard": result.text,
        "error_rate": round(rate, 3),
        "script": in_script(result.text, item["language"]),
        "cost": audio_cost(settings.transcribe_model, seconds) or 0.0,
        "seconds": time.monotonic() - started,
    }


async def main(label: str, repeat: int) -> None:
    items = load(DATASETS / "voice.json")["items"]
    rows = await asyncio.gather(*(hear(item) for item in items for _ in range(repeat)))
    scores = {
        "heard_right": share(sum(r["error_rate"] <= MAX_ERROR_RATE for r in rows), len(rows)),
        "error_rate": mean([r["error_rate"] for r in rows], 3),
        "script": share(sum(r["script"] for r in rows), len(rows)),
    }
    times = sorted(r["seconds"] for r in rows)
    spent = round(sum(r["cost"] for r in rows), 4)
    run = run_record(
        model=settings.transcribe_model,
        repeat=repeat,
        scores=scores,
        cost=spent,
        median_seconds=round(times[len(times) // 2], 1),
    )
    save(RESULTS / f"transcription_{label}.json", {"run": run, "rows": rows})
    print(json.dumps({"scores": scores, "cost": spent}, indent=1))

    for r in rows:
        if r["error_rate"] > MAX_ERROR_RATE or not r["script"]:
            print(f"- {r['id']}: {r['error_rate']} {r['heard']!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(main(args.label, args.repeat))
