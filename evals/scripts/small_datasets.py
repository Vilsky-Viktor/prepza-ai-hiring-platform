"""Checks by code of the small utility prompts' datasets (code-language tags, translations,
quality patterns, titles) and of the judge's question times, for check_datasets.py: each says what it is, has unique ids, and
its expectations fit its own text. Each returns the texts to check against prompts' examples."""

import json
import re
from collections import Counter
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
DATASETS = EVALS / "datasets"
SERVICES = EVALS.parent / "services"


def load(name: str):
    return json.loads((DATASETS / name).read_text())


def check_described(name: str, data: dict, problems: list[str]) -> None:
    """A hand-made or built set says what it is, when and with what it was made."""
    for key in ("about", "built", "model"):
        if key not in data:
            problems.append(f"{name}: no {key!r} (what it is, when and with what it was built)")


def unique_ids(name: str, rows: list[dict], problems: list[str]) -> None:
    ids = Counter(row["id"] for row in rows)
    problems += [f"{name}: id {i} appears {n} times" for i, n in ids.items() if n > 1]


def check_code_languages(problems: list[str]) -> list[str]:
    """Every expected notation is one the site colors; returns the examples."""
    data = load("code_languages.json")
    known = set(
        re.findall(
            r'"(\w+)"', (SERVICES / "generation/src/generation/constants/code.py").read_text()
        )
    )
    check_described("code_languages.json", data, problems)
    unique_ids("code_languages.json", data["items"], problems)
    problems += [
        f"code_languages.json: {item['id']} expects an unknown notation {item['expect']!r}"
        for item in data["items"]
        if item["expect"] not in known
    ]

    return [item["example"] for item in data["items"]]


def check_translations(problems: list[str]) -> list[str]:
    """Every text has its fields and what code checks; returns the texts."""
    data = load("translations.json")
    rows = data["news"] + data["campaigns"]
    check_described("translations.json", data, problems)
    unique_ids("translations.json", rows, problems)

    for row in rows:
        fields = ("title", "text") if row in data["news"] else ("subject", "text", "button")

        if any(field not in row for field in (*fields, "keep")):
            problems.append(f"translations.json: {row['id']} lacks a field")

        source = " ".join(str(row.get(field) or "") for field in fields)
        problems += [
            f"translations.json: {row['id']} keeps {name!r}, which its text lacks"
            for name in row["keep"] + row.get("links", []) + row.get("numbers", [])
            if name not in source
        ]

    return [row["text"] for row in rows]


def check_patterns(problems: list[str]) -> list[str]:
    """Planted questions exist in their group; returns the questions' texts."""
    data = load("patterns.json")
    check_described("patterns.json", data, problems)
    unique_ids("patterns.json", data["groups"], problems)

    for group in data["groups"]:
        for planted in group["planted"]:
            if not all(1 <= n <= len(group["questions"]) for n in planted["questions"]):
                problems.append(f"patterns.json: {planted['id']} cites a missing question")

        if group["expect_none"] == bool(group["planted"]):
            problems.append(f"patterns.json: {group['id']} plants mistakes but expects none")

    if {t["same"] for t in data["judge_traps"]} != {True, False}:
        problems.append("patterns.json: judge_traps need matching and non-matching pairs")

    return [q["text"] for group in data["groups"] for q in group["questions"]]


def check_titles(problems: list[str]) -> list[str]:
    """Each conversation's language is the site's, and what it forbids is in it."""
    data = load("titles.json")
    known = set(
        re.findall(
            r'"(\w+)": "',
            (EVALS.parent / "packages/common/src/prepza_common/config/constants.py").read_text(),
        )
    )
    check_described("titles.json", data, problems)
    unique_ids("titles.json", data["items"], problems)

    for item in data["items"]:
        text = " ".join(m["text"] for m in item["messages"])

        if item["language"] not in known or not item.get("expect"):
            problems.append(f"titles.json: {item['id']} lacks a known language or an expectation")

        problems += [
            f"titles.json: {item['id']} forbids {word!r}, which it never says"
            for word in item["forbidden"]
            if word not in text
        ]

    return [m["text"] for item in data["items"] for m in item["messages"]]


def check_postings(problems: list[str]) -> list[str]:
    """Each posting has its expectations, and each revision a planned posting to start from."""
    data = load("postings.json")
    inputs = {d["id"] for d in load("inputs.json")["domains"]}
    check_described("postings.json", data, problems)
    unique_ids("postings.json", data["postings"] + data["revisions"], problems)
    planned = {p["id"] for p in data["postings"]} | set(data["from_inputs"])
    problems += [
        f"postings.json: {i} isn't in inputs.json" for i in data["from_inputs"] if i not in inputs
    ]

    for posting in data["postings"]:
        if not posting.get("must_cover") or posting.get("level") not in ("basic", "medium", "hard"):
            problems.append(f"postings.json: {posting['id']} lacks what it must cover or a level")

        problems += [
            f"postings.json: {posting['id']} forbids {word!r}, which it never says"
            for word in posting.get("forbidden_in_template", [])
            if word not in posting["text"]
        ]

    problems += [
        f"postings.json: {r['id']} starts from {r['from']}, which isn't planned"
        for r in data["revisions"]
        if r["from"] not in planned
    ]

    return [p["text"] for p in data["postings"]] + [r["instructions"] for r in data["revisions"]]


def check_duplicates(problems: list[str]) -> list[str]:
    """Pairs of both kinds, each pair two different texts."""
    data = load("duplicates.json")
    check_described("duplicates.json", data, problems)
    unique_ids("duplicates.json", data["items"], problems)

    if {item["same"] for item in data["items"]} != {True, False}:
        problems.append("duplicates.json: needs pairs that ask the same and pairs that don't")

    problems += [
        f"duplicates.json: {item['id']} pairs a text with itself"
        for item in data["items"]
        if item["a"] == item["b"]
    ]

    return [text for item in data["items"] for text in (item["a"], item["b"])]


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


def check_question_times(problems: list[str]) -> list[str]:
    """The judge's seconds: each for a question of its set, once, a whole number above 0."""
    data = load("question_times.json")
    check_described("question_times.json", data, problems)
    known = {
        (name, item["id"])
        for name in ("questions.json", "multi_questions.json", "language_questions.json")
        for item in load(name)["items"]
    }
    seen = Counter((item["set"], item["id"]) for item in data["items"])
    problems += [
        f"question_times.json: {key} appears {n} times" for key, n in seen.items() if n > 1
    ]
    problems += [f"question_times.json: no question {key}" for key in seen if key not in known]
    problems += [
        f"question_times.json: {item['id']} has no whole seconds above 0"
        for item in data["items"]
        if not all(
            isinstance(item.get(k, 1), int) and item.get(k, 1) > 0 for k in ("seconds", "retest")
        )
        or "seconds" not in item
    ]

    return []


def check_screen(problems: list[str]) -> list[str]:
    """Texts of both kinds, each with a language."""
    data = load("screen.json")
    check_described("screen.json", data, problems)
    unique_ids("screen.json", data["items"], problems)

    if {item["accept"] for item in data["items"]} != {True, False}:
        problems.append("screen.json: needs texts to accept and texts to refuse")

    return [item["text"] for item in data["items"]]
