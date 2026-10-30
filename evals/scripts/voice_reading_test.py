"""Tests voice mode's reading aloud on datasets/voice_reading.json: each question is turned into
the interviewer's script by rounds' own code (question_script), read by its own call (the speech
model and voice in settings, services/voice_clips.py speak), then heard by its transcription model,
and code compares what was heard with the script: the word error rate, every option's letter
heard, and nothing added (no run of ADDED_WORDS or more words the script hasn't, such as an answer
or a comment). The transcription's own errors count too, alike for every speech model.

    evals/run.sh rounds voice_reading_test.py --label base     # --repeat 2

Costs about ten cents a repeat."""

import argparse
import asyncio
import json
import re
import time

from common import DATASETS, RESULTS, load, run_record, save
from prepza_common.ai.llm import audio_cost
from prepza_common.ai.speech import audio_seconds, speech_to_text
from stats import mean, share
from prepza_common.ai.spoken_words import word_errors

from rounds.config import settings
from rounds.constants.voice import LETTERS, MAX_ANSWER_SECONDS
from rounds.helpers.voice_speech import ogg_seconds, question_script
from rounds.integrations.llm import get_transcribe_client
from rounds.schemas.rounds import NextQuestion
from rounds.services.voice_clips import speak

# A reading is heard right at most at this word error rate.
MAX_WORD_ERRORS = 0.1
# This many words in a row that the script hasn't is something added, not a mishearing.
ADDED_WORDS = 3
MAX_CONCURRENCY = 6


def letter_heard(letter: str, heard: str) -> bool:
    """The option's letter as a word of its own ("B:", "B."), not the start of "B-tree"."""
    return re.search(rf"(?<![\w-]){letter}(?![\w-])", heard) is not None


async def one(item: dict, slots: asyncio.Semaphore) -> dict:
    question = NextQuestion(
        question_id="00000000-0000-0000-0000-000000000000",
        number=1,
        text=item["text"],
        options=item["options"],
        multi=item["multi"],
    )
    script = question_script(question, item["language"])

    async with slots:
        started = time.monotonic()
        audio, spoken = await speak(script, item["language"])
        took = time.monotonic() - started
        model = settings.transcribe_model
        result = await speech_to_text(
            get_transcribe_client(), model, "audio.ogg", audio, "audio/ogg", item["language"]
        )

    heard = result.text.strip()
    rate, added = word_errors(script, heard)
    heard_seconds = audio_seconds(getattr(result, "usage", None), len(audio), MAX_ANSWER_SECONDS)

    return {
        "id": item["id"],
        "script": script,
        "heard": heard,
        "word_errors": round(rate, 3),
        "letters": all(letter_heard(LETTERS[i], heard) for i in range(len(item["options"]))),
        "added": added,
        "seconds": ogg_seconds(audio),
        "speech_cost": audio_cost(settings.speech_model, spoken) or 0.0,
        "hearing_cost": audio_cost(model, heard_seconds) or 0.0,
        "took": took,
    }


async def main(label: str, repeat: int) -> None:
    items = load(DATASETS / "voice_reading.json")["items"]
    slots = asyncio.Semaphore(MAX_CONCURRENCY)
    rows = await asyncio.gather(*(one(item, slots) for item in items for _ in range(repeat)))
    scores = {
        "heard_right": share(sum(r["word_errors"] <= MAX_WORD_ERRORS for r in rows), len(rows)),
        "word_errors": mean([r["word_errors"] for r in rows], 3),
        "letters": share(sum(r["letters"] for r in rows), len(rows)),
        "nothing_added": share(sum(r["added"] < ADDED_WORDS for r in rows), len(rows)),
    }
    times = sorted(r["took"] for r in rows)
    speech = round(sum(r["speech_cost"] for r in rows), 4)
    run = run_record(
        model=f"{settings.speech_model} ({settings.speech_voice})",
        transcribe_model=settings.transcribe_model,
        repeat=repeat,
        scores=scores,
        cost=round(speech + sum(r["hearing_cost"] for r in rows), 4),
        speech_cost=speech,
        audio_minutes=round(sum(r["seconds"] for r in rows) / 60, 2),
        median_seconds=round(times[len(times) // 2], 1),
    )
    save(RESULTS / f"voice_reading_{label}.json", {"run": run, "rows": rows})
    print(json.dumps(run, indent=1))

    for r in rows:
        if r["word_errors"] > MAX_WORD_ERRORS or not r["letters"] or r["added"] >= ADDED_WORDS:
            print(f"- {r['id']}: {r['word_errors']} added {r['added']}\n  {r['heard']!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(main(args.label, args.repeat))
