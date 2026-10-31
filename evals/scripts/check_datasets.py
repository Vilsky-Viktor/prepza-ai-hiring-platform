"""Checks the frozen datasets by code, for free: their shape, duplicates, overlap with the
examples in our prompts, and what they cover. Runs on the host, no container needed:

    python3 evals/scripts/check_datasets.py

Prints each problem and a coverage table, and exits 1 when there is a problem."""

import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "common" / "tests"))

from service_code import service_code
from small_datasets import (
    check_ai_picks,
    check_code_languages,
    check_duplicates,
    check_pattern_gate,
    check_patterns,
    check_postings,
    check_question_times,
    check_screen,
    check_titles,
    check_translations,
)
from voice_datasets import (
    check_voice,
    check_voice_answers,
    check_voice_reading,
    check_voice_sounds,
)

EVALS = Path(__file__).resolve().parents[1]
DATASETS = EVALS / "datasets"
# The keys of the pages the panel opens on (an unknown one reaches the model as no key).
PAGE_KEYS = EVALS.parent / "packages/common/src/testee_common/ai/page_keys.py"
QUESTION_SETS = ("questions.json", "multi_questions.json", "language_questions.json")
TRAP_SETS = {"key_traps.json": "questions.json", "multi_key_traps.json": "multi_questions.json"}
# Two questions of one subtopic this alike, options included, are the same question reworded.
NEAR_DUPLICATE = 0.9
# A quoted example in a prompt of this many words or more must not appear in a dataset; the
# product's own terms, quoted in prompts too, may.
MIN_EXAMPLE_WORDS = 4
PRODUCT_TERMS = {"select all that apply"}
# Names, not examples: the titles AI apps show for the MCP server's tools (the in-app assistant's
# model never reads them), so a dataset may say "set the pass mark".
NOT_EXAMPLES = {"mcp_titles.py"}
ACTION_KINDS = {
    "create",
    "invite",
    "edit",
    "delete",
    "buy",
    "connect",
    "cross",
    "injection",
    "features",
}


def load(name: str):
    return json.loads((DATASETS / name).read_text())


def normal(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()


def full_text(item: dict) -> str:
    return normal(" ".join([item["question"], *(o["answer"] for o in item["options"])]))


def prompt_examples() -> set[str]:
    """The quoted examples in every service's prompts and tool descriptions."""
    found = set()

    for path in [
        *service_code(EVALS.parent, "prompts/*.py"),
        *service_code(EVALS.parent, "constants/*.py"),
    ]:
        if path.name in NOT_EXAMPLES:
            continue

        for quoted in re.findall(r'"([^"\n{}]+)"', path.read_text()):
            if len(quoted.split()) >= MIN_EXAMPLE_WORDS and normal(quoted) not in PRODUCT_TERMS:
                found.add(normal(quoted))

    return found


def check_questions(name: str, items: list[dict], problems: list[str]) -> None:
    ids = Counter(item["id"] for item in items)
    problems += [f"{name}: id {i} appears {n} times" for i, n in ids.items() if n > 1]

    for item in items:
        answers = [option["answer"] for option in item["options"]]
        marked = sum(option["correct"] for option in item["options"])

        if len(answers) != 4 or len({answer.strip().lower() for answer in answers}) != 4:
            problems.append(f"{name}: {item['id']} needs 4 different options")

        if marked not in (1, 2, 3):
            problems.append(f"{name}: {item['id']} has {marked} options marked correct")

        if not all(item.get(key) for key in ("domain", "level", "topic", "subtopic", "question")):
            problems.append(f"{name}: {item['id']} lacks a field")

    by_subtopic: dict[str, list[dict]] = {}

    for item in items:
        by_subtopic.setdefault(item["subtopic"], []).append(item)

    for group in by_subtopic.values():
        for i, first in enumerate(group):
            for second in group[i + 1 :]:
                alike = SequenceMatcher(None, full_text(first), full_text(second))

                if alike.ratio() >= NEAR_DUPLICATE:
                    problems.append(f"{name}: {first['id']} and {second['id']} are near duplicates")


def check_traps(name: str, source: str, problems: list[str]) -> None:
    originals = {item["id"]: item for item in load(source)["items"]}

    for trap in load(name)["items"]:
        original = originals.get(trap["id"].removeprefix("trap-"))

        if original is None or trap.get("expected_key_correct") is not False:
            problems.append(f"{name}: {trap['id']} has no original or no expected verdict")
        elif trap["options"] == original["options"]:
            problems.append(f"{name}: {trap['id']} keeps the original key")


def check_assistant(problems: list[str]) -> list[str]:
    """Ids, pages and expectations of the assistant's sets; returns every question's text."""
    questions = load("assistant_questions.json")
    guides = load("assistant_guides.json")
    rows = questions["general"] + questions["page"] + guides["guide"]
    ids = Counter(row["id"] for row in rows)
    problems += [f"assistant: id {i} appears {n} times" for i, n in ids.items() if n > 1]
    general = {row["id"] for row in questions["general"]}
    problems += [
        f"assistant_guides: {i} isn't a general question"
        for i in guides["general"]
        if i not in general
    ]

    for row in rows:
        if row["page"] not in questions["pages"] or not row.get("expect"):
            problems.append(f"assistant: {row['id']} lacks a known page or an expectation")

    return [row["question"] for row in rows]


def check_actions(problems: list[str]) -> list[str]:
    """The action set's ids, pages, kinds and expectations; returns its messages."""
    data = load("assistant_actions.json")
    cases = data["cases"]
    ids = Counter(case["id"] for case in cases)
    problems += [f"assistant_actions: id {i} appears {n} times" for i, n in ids.items() if n > 1]

    for case in cases:
        expect = case.get("expect")

        if case["page"] not in data["pages"] or case["kind"] not in ACTION_KINDS:
            problems.append(f"assistant_actions: {case['id']} lacks a known page or kind")

        if expect is None or set(expect) - {"actions", "ask", "link", "warn"}:
            problems.append(f"assistant_actions: {case['id']} has no known expectation")

    known = set(re.findall(r'"(\w+)"', PAGE_KEYS.read_text()))
    problems += [
        f"assistant_actions: page {name} has an unknown key {page['key']!r}"
        for name, page in data["pages"].items()
        if page["key"] not in known
    ]

    for trap in data["judge_traps"]:
        if trap["case"] not in ids:
            problems.append(f"assistant_actions: judge trap {trap['id']} names no case")

    return [case["message"] for case in cases]


def main() -> None:
    problems: list[str] = []
    examples = prompt_examples()
    texts: list[tuple[str, str]] = []
    coverage = Counter()
    every_question: dict[str, str] = {}

    for name in QUESTION_SETS:
        if not (DATASETS / name).exists():
            continue

        data = load(name)
        items = data["items"]
        check_questions(name, items, problems)

        for key in ("about", "built", "model"):
            if key not in data:
                problems.append(f"{name}: no {key!r} (what it is, when and with what it was built)")

        for item in items:
            kind = "multi" if sum(o["correct"] for o in item["options"]) > 1 else "single"
            language = item.get("language", "en")
            coverage[(name, item["domain"], item["level"], language, kind)] += 1
            texts.append((f"{name} {item['id']}", item["question"]))
            seen = every_question.setdefault(normal(item["question"]), f"{name} {item['id']}")

            if seen != f"{name} {item['id']}":
                problems.append(f"{name}: {item['id']} repeats {seen}")

    for name, source in TRAP_SETS.items():
        check_traps(name, source, problems)

    texts += [("assistant", text) for text in check_assistant(problems)]
    texts += [("assistant_actions", text) for text in check_actions(problems)]
    texts += [("code_languages", text) for text in check_code_languages(problems)]
    texts += [("translations", text) for text in check_translations(problems)]
    texts += [("patterns", text) for text in check_patterns(problems)]
    texts += [("pattern gate", text) for text in check_pattern_gate(problems)]
    texts += [("titles", text) for text in check_titles(problems)]
    texts += [("postings", text) for text in check_postings(problems)]
    texts += [("duplicates", text) for text in check_duplicates(problems)]
    texts += [("voice", text) for text in check_voice(problems)]
    texts += [("voice answers", text) for text in check_voice_answers(problems)]
    texts += [("voice reading", text) for text in check_voice_reading(problems)]
    check_voice_sounds(problems)
    texts += [("screen", text) for text in check_screen(problems)]
    check_question_times(problems)
    check_ai_picks(problems)

    for where, text in texts:
        for example in examples:
            if example in normal(text):
                problems.append(f"{where} contains a prompt's example: {example!r}")

    print("coverage (dataset, domain, level, language, kind: questions):")

    for key, count in sorted(coverage.items()):
        print("  ", ", ".join(key), count)

    for problem in problems:
        print("-", problem)

    print(f"{len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
