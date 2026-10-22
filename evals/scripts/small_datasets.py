"""Checks by code of the small utility prompts' datasets (code-language tags, translations,
quality patterns, titles), for check_datasets.py: each says what it is, has unique ids, and
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
    known = set(re.findall(r'"(\w+)"', (SERVICES / "generation/app/constants/code.py").read_text()))
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
            (EVALS.parent / "packages/common/src/prepza_common/constants.py").read_text(),
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
