"""Checks by code of the speech datasets, for check_datasets.py: the assistant's voice messages,
voice mode's spoken answers, its readings and the sounds it must ignore. Each says what it is, has
unique ids and its recordings, and returns the texts to check against prompts' examples."""

import re

from small_datasets import DATASETS, EVALS, check_described, load, unique_ids

# Voice mode's options, by index: four to a question.
OPTIONS = 4
INTENTS = {"choose", "confirm", "reject", "unclear"}
# The languages a test may be taken by voice in, read from the shared constants (this check runs
# without the package installed).
CONSTANTS = EVALS.parent / "packages/common/src/testee_common/config/constants.py"
VOICE_LANGUAGES = set(
    re.findall(r'"(\w+)"', re.search(r"VOICE_LANGUAGES = \((.*)\)", CONSTANTS.read_text())[1])
)


def check_voice(problems: list[str]) -> list[str]:
    """Every message has its recording."""
    data = load("voice.json")
    check_described("voice.json", data, problems)
    unique_ids("voice.json", data["items"], problems)
    problems += [
        f"voice.json: {item['id']} has no audio/{item['id']}.ogg (build_audio.py)"
        for item in data["items"]
        if not (DATASETS / "audio" / f"{item['id']}.ogg").exists()
    ]

    return [item["text"] for item in data["items"]]


def check_voice_answers(problems: list[str]) -> list[str]:
    """Each answer is to a known question in its language, expects an intent and options that
    exist (a choice of one on a single-answer question, none when unclear or a no), and a
    spoken one has its recording."""
    name = "voice_answers.json"
    data = load(name)
    check_described(name, data, problems)
    unique_ids(name, data["items"], problems)

    for item in data["items"]:
        question = data["questions"].get(item["question"])
        picks = item["picks"]

        if question is None or question["language"] != item["language"]:
            problems.append(f"{name}: {item['id']} has no question in its language")
            continue

        if item["intent"] not in INTENTS or any(not 0 <= p < OPTIONS for p in picks):
            problems.append(f"{name}: {item['id']} expects an unknown intent or option")

        if (item["intent"] in ("choose", "confirm")) != bool(picks) or (
            item["intent"] == "choose" and not question["multi"] and len(picks) != 1
        ):
            problems.append(f"{name}: {item['id']} expects options its intent can't have")

        if "spoken" in item and not (DATASETS / "audio" / f"answer_{item['id']}.ogg").exists():
            problems.append(f"{name}: {item['id']} has no audio (build_voice_answers.py)")

    return [item["said"] for item in data["items"]]


def check_voice_reading(problems: list[str]) -> list[str]:
    """Each question is in a voice language with four options."""
    name = "voice_reading.json"
    data = load(name)
    check_described(name, data, problems)
    unique_ids(name, data["items"], problems)
    problems += [
        f"{name}: {item['id']} needs a voice language and {OPTIONS} options"
        for item in data["items"]
        if item["language"] not in VOICE_LANGUAGES or len(item["options"]) != OPTIONS
    ]

    return [item["text"] for item in data["items"]]


def check_voice_sounds(problems: list[str]) -> None:
    """Each sound has its formula (or a made-up message to play) and its recording."""
    name = "voice_sounds.json"
    data = load(name)
    check_described(name, data, problems)
    unique_ids(name, data["items"], problems)
    problems += [
        f"{name}: {item['id']} has no audio/sound_{item['id']}.ogg (build_voice_sounds.py)"
        for item in data["items"]
        if not (DATASETS / "audio" / f"sound_{item['id']}.ogg").exists()
        or ("source" in item) == ("speech" in item)
    ]
