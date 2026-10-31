"""Tests voice mode's matching on datasets/voice_answers.json: each answer, as text (what speech
recognition would give) and, for the `spoken` ones, also as audio (audio/answer_<id>.ogg, heard
by the service's own speech-to-text first), goes through rounds' own matching call
(services/voice_match.py), and code grades the intent and the options picked. A wrong match
(options the candidate didn't say, recorded as theirs) is the failure that matters most; an
unclear one only asks again. datasets/voice_sounds.json's sounds (a cough, a door, thunder: no
speech) are heard the same way and must come back as noise, which the browser ignores; any other
intent is a reaction (Mira asks again).

    evals/run.sh rounds voice_answers_test.py --label base     # --repeat 2, --only en01,de04
    evals/run.sh rounds voice_answers_test.py --hearing live --label streamed
    evals/run.sh rounds voice_answers_test.py --hearing live --live-model gpt-live-transcribe \
        --delay low --label live-low

MODEL and EFFORT test another matching model. `--hearing live` streams the spoken answers as voice
mode does while the candidate speaks (voice_live.py: rounds' realtime transcription session, in
real time; `--live-model` and its `--delay` try another model) instead of sending whole
recordings, and reports how long the final text took after each answer's end; `--no-keywords`
leaves out the recognition hints. Costs about a cent a repeat (gpt-live-transcribe: about five)."""

import argparse
import asyncio
import json
import os
import time
from collections import defaultdict

from common import DATASETS, RESULTS, cost, load, run_record, save
from openai import OpenAIError
from stats import share
from testee_common.ai.llm import audio_cost
from testee_common.ai.speech import audio_seconds, speech_to_text
from voice_live import hear_live

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


async def hear(data: dict, item: dict, args) -> tuple[str, float, float | None]:
    """What the service hears: (text, cost, seconds from the answer's end to the final text when
    heard live)."""
    name = f"sound_{item['id']}" if "sound" in item else f"answer_{item['id']}"
    path = DATASETS / "audio" / f"{name}.ogg"
    keywords = hearing_keywords(question_of(data, item))

    if args.hearing == "live":
        # A session that fails is a failure here; voice mode would send the recording whole.
        try:
            hints = [] if args.no_keywords else keywords
            return await hear_live(path, item["language"], hints, args.live_model, args.delay)
        except (TimeoutError, OpenAIError) as error:
            print(f"- live hearing failed {item['id']}: {type(error).__name__}")

            return None, 0.0, None

    audio = path.read_bytes()
    model = settings.transcribe_model
    result = await speech_to_text(
        get_transcribe_client(),
        model,
        "audio.ogg",
        audio,
        "audio/ogg",
        item["language"],
        keywords,
    )
    seconds = audio_seconds(getattr(result, "usage", None), len(audio), MAX_ANSWER_SECONDS)

    return result.text.strip(), audio_cost(model, seconds) or 0.0, None


async def one(data: dict, item: dict, spoken: bool, slots: asyncio.Semaphore, args) -> dict:
    async with slots:
        started = time.monotonic()
        said, heard_cost, final = (
            await hear(data, item, args) if spoken else (item["said"], 0, None)
        )
        if said is None:
            intent, picks, usage = Intent.UNCLEAR, [], None
        else:
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
        "final_seconds": final,
        "failed": said is None,
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
        "hearing_failed": share(sum(r["failed"] for r in rows), n),
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
        *(one(data, item, spoken, slots, args) for item, spoken in jobs for _ in range(args.repeat))
    )
    answers = [r for r in rows if not r["sound"]]
    scores = {
        "text": scores_of([r for r in answers if not r["spoken"]]),
        "spoken": scores_of([r for r in answers if r["spoken"]]),
        "sounds": sound_scores([r for r in rows if r["sound"]]),
    }
    times = sorted(r["seconds"] for r in rows)
    spent = round(sum(r["cost"] for r in rows), 4)
    finals = sorted(r["final_seconds"] for r in rows if r["final_seconds"] is not None)
    hearing = (
        f"{args.live_model} ({args.delay or 'no delay'}"
        f"{', no keywords' if args.no_keywords else ''}, streamed)"
        if args.hearing == "live"
        else settings.transcribe_model
    )
    run = run_record(
        model=f"{settings.voice_match_model} ({settings.voice_match_reasoning_effort}), "
        f"hearing {hearing}",
        repeat=args.repeat,
        scores=scores,
        cost=spent,
        median_seconds=round(times[len(times) // 2], 2),
        p90_seconds=round(times[int(len(times) * 0.9)], 2),
        final_median_seconds=round(finals[len(finals) // 2], 2) if finals else None,
        final_p90_seconds=round(finals[int(len(finals) * 0.9)], 2) if finals else None,
    )
    save(RESULTS / f"voice_answers_{args.label}.json", {"run": run, "rows": rows})
    print(
        json.dumps(
            {
                "scores": scores,
                "cost": spent,
                "median_seconds": run["median_seconds"],
                "p90_seconds": run["p90_seconds"],
                "final_median_seconds": run["final_median_seconds"],
                "final_p90_seconds": run["final_p90_seconds"],
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
    parser.add_argument("--hearing", choices=("recording", "live"), default="recording")
    parser.add_argument("--live-model", default=settings.transcribe_model)
    parser.add_argument("--delay", default="")
    parser.add_argument("--no-keywords", action="store_true")
    asyncio.run(main(parser.parse_args()))
