"""Checks by code of the speech datasets, for check_datasets.py: the assistant's voice messages
and voice mode's spoken answers. Each says what it is, has unique ids and its recordings, and
returns the texts to check against prompts' examples."""

from small_datasets import DATASETS, check_described, load, unique_ids

# Voice mode's options, by index: four to a question.
OPTIONS = 4
INTENTS = {"choose", "confirm", "reject", "unclear"}


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
