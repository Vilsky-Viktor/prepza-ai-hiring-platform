"""Tests voice mode's matching on datasets/voice_answers.json: each answer, as text (what speech
recognition would give) and, for the `spoken` ones, also as audio (audio/answer_<id>.ogg, heard
by the service's own speech-to-text first), goes through rounds' own matching call
(services/voice_match.py), and code grades the intent and the options picked. A wrong match
(options the candidate didn't say, recorded as theirs) is the failure that matters most; an
unclear one only asks again. datasets/voice_sounds.json's sounds (a cough, a door, thunder: no
speech) are heard the same way and must come back as noise, which the browser ignores; any other
intent is a reaction (Mira asks again).

    evals/run.sh rounds voice_answers_test.py --label base     # --repeat 2, --only en01,de04

MODEL and EFFORT test another matching model. Costs about a cent a repeat."""

import argparse
import asyncio
import json
import os
import time
from collections import defaultdict

from common import DATASETS, RESULTS, cost, load, run_record, save
from prepza_common.ai.llm import audio_cost
from prepza_common.ai.speech import audio_seconds, speech_to_text
from stats import share

from rounds.config import settings
from rounds.constants.voice import MAX_ANSWER_SECONDS, Intent
from rounds.helpers.voice_match import hearing_keywords
from rounds.integrations.llm import get_transcribe_client
from rounds.schemas.rounds import NextQuestion
from rounds.services.voice_match import match

if "MODEL" in os.environ:
    settings.voice_match_model = os.environ["MODEL"]

if "EFFORT" in os.environ:
    settings.voice_match_reasoning_effort = os.environ["EFFORT"]

PICKING = (Intent.CHOOSE, Intent.CONFIRM)
# Sounds are heard as a question of en1 would be, with nothing waiting.
SOUND = {
    "sound": True,
    "language": "en",
    "question": "en1",
    "waiting": [],
    "intent": "noise",
    "picks": [],
}
MAX_CONCURRENCY = 8


def question_of(data: dict, item: dict) -> NextQuestion:
    found = data["questions"][item["question"]]

    return NextQuestion(
        question_id="00000000-0000-0000-0000-000000000000",
        number=1,
        text=found["text"],
        options=found["options"],
        multi=found["multi"],
    )


async def hear(data: dict, item: dict) -> tuple[str, float]:
    name = f"sound_{item['id']}" if "sound" in item else f"answer_{item['id']}"
    audio = (DATASETS / "audio" / f"{name}.ogg").read_bytes()
    model = settings.transcribe_model
    result = await speech_to_text(
        get_transcribe_client(),
        model,
        "audio.ogg",
        audio,
        "audio/ogg",
        item["language"],
        hearing_keywords(question_of(data, item)),
    )
    seconds = audio_seconds(getattr(result, "usage", None), len(audio), MAX_ANSWER_SECONDS)

    return result.text.strip(), audio_cost(model, seconds) or 0.0


async def one(data: dict, item: dict, spoken: bool, slots: asyncio.Semaphore) -> dict:
    async with slots:
        started = time.monotonic()
        said, heard_cost = await hear(data, item) if spoken else (item["said"], 0.0)
        intent, picks, usage = await match(
            question_of(data, item), said, item["waiting"], item["language"], item["id"]
        )

    right = intent == item["intent"] and picks == item["picks"]

    return {
        "id": item["id"],
        "language": item["language"],
        "kind": item["kind"],
        "sound": "sound" in item,
        "spoken": spoken,
        "said": said,
        "intent": intent,
        "picks": picks,
        "right": right,
        # Options recorded that the candidate didn't choose (or a choice where they chose none).
        "wrong_match": intent in PICKING and not right,
        # Read by code, without a matching call (a plain yes, a letter alone).
        "by_code": usage is None,
        "cost": (cost(settings.voice_match_model, usage) if usage else 0.0) + heard_cost,
        "seconds": time.monotonic() - started,
    }


def sound_scores(rows: list[dict]) -> dict:
    """Sounds that got a reaction (any intent but noise), the target 0."""
    return {"reacted": share(sum(r["intent"] != "noise" for r in rows), len(rows))}


def scores_of(rows: list[dict]) -> dict:
    n = len(rows)
    by_language = defaultdict(list)

    for row in rows:
        by_language[row["language"]].append(row)

    return {
        "right": share(sum(r["right"] for r in rows), n),
        "wrong_matches": share(sum(r["wrong_match"] for r in rows), n),
        "by_code": share(sum(r["by_code"] for r in rows), n),
        # Read by code and not what the candidate meant: the target is none.
        "by_code_wrong": share(sum(r["by_code"] and not r["right"] for r in rows), n),
        "unclear_when_chosen": share(
            sum(r["intent"] == Intent.UNCLEAR and not r["right"] for r in rows), n
        ),
        **{
            f"right_{language}": share(sum(r["right"] for r in found), len(found))
            for language, found in sorted(by_language.items())
        },
    }


async def main(args) -> None:
    data = load(DATASETS / "voice_answers.json")
    items = [i for i in data["items"] if not args.only or i["id"] in args.only.split(",")]
    slots = asyncio.Semaphore(MAX_CONCURRENCY)
    sounds = [
        {**SOUND, **sound}
        for sound in load(DATASETS / "voice_sounds.json")["items"]
        if not args.only or sound["id"] in args.only.split(",")
    ]
    jobs = [(item, False) for item in items] + [(i, True) for i in items if "spoken" in i]
    jobs += [(sound, True) for sound in sounds]
    rows = await asyncio.gather(
        *(one(data, item, spoken, slots) for item, spoken in jobs for _ in range(args.repeat))
    )
    answers = [r for r in rows if not r["sound"]]
    scores = {
        "text": scores_of([r for r in answers if not r["spoken"]]),
        "spoken": scores_of([r for r in answers if r["spoken"]]),
        "sounds": sound_scores([r for r in rows if r["sound"]]),
    }
    times = sorted(r["seconds"] for r in rows)
    spent = round(sum(r["cost"] for r in rows), 4)
    run = run_record(
        model=f"{settings.voice_match_model} ({settings.voice_match_reasoning_effort}), "
        f"hearing {settings.transcribe_model}",
        repeat=args.repeat,
        scores=scores,
        cost=spent,
        median_seconds=round(times[len(times) // 2], 2),
        p90_seconds=round(times[int(len(times) * 0.9)], 2),
    )
    save(RESULTS / f"voice_answers_{args.label}.json", {"run": run, "rows": rows})
    print(
        json.dumps(
            {
                "scores": scores,
                "cost": spent,
                "median_seconds": run["median_seconds"],
                "p90_seconds": run["p90_seconds"],
            },
            indent=1,
            ensure_ascii=False,
        )
    )

    for r in rows:
        if not r["right"]:
            mark = ("WRONG" if r["wrong_match"] else "miss") + (" by code" if r["by_code"] else "")
            print(
                f"- {mark} {r['id']}{' spoken' if r['spoken'] else ''} [{r['kind']}]: "
                f"{r['said']!r} -> {r['intent']} {r['picks']}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--only", default="")
    asyncio.run(main(parser.parse_args()))
