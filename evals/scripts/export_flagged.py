"""Exports flagged questions into datasets/flagged_traps.json, as traps for the verifier
(verify_test.py) and the judge (review_questions.py), so the evals measure the mistakes we
actually see. Runs in library's container, free:

    evals/run.sh library export_flagged.py

Only platform templates' questions, word for word, as they were when flagged (the version a
replacement took over, or the question now while it's still flagged); the evals' own throwaway
templates (assistant_fixture.TEMPLATES) are left out. What each is a trap for: flagged_labels.py.
Companies' questions: company_questions() below. A question already in the dataset stays as it
is (frozen); new ones are added."""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from assistant_fixture import TEMPLATES
from flagged_labels import trap, trap_id

from library.core.db import Session
from library.helpers.quality import replacement
from library.repositories import quality_signals

DATASET = Path(__file__).resolve().parents[1] / "datasets" / "flagged_traps.json"
# The evals' own templates (assistant_templates.py): placeholders, not questions anyone wrote.
THROWAWAY = {title for title, _ in TEMPLATES}
ABOUT = (
    "Platform templates' flagged questions, word for word as they were when flagged, exported by "
    "export_flagged.py: traps for the verifier and the judge (flagged_labels.py). A wrong key only "
    "once a replacement with the same options moved it (expected_key_correct false, right_key); "
    "weak options and rewrites by their flag. Never a company's question. See datasets/README.md."
)


def company_questions() -> list[dict]:
    """Companies' flagged questions: none until the shared question bank's filter exists (no
    company, product, person or place details). Then only questions that pass it, never one from
    an interview kept out of the bank (`keep_private`), and no other company text in a dataset."""
    return []


def as_trap(text, options, flag, topic, template, replaced_by) -> dict | None:
    label = trap(flag, options, replaced_by)

    if label is None or template.title in THROWAWAY:
        return None

    return {
        "id": trap_id(text, options),
        "flag": flag,
        "level": template.level,
        "language": template.language,
        "topic": topic.title,
        "question": text,
        "options": options,
        **label,
    }


async def flagged() -> list[dict]:
    async with Session() as session:
        now = await quality_signals.flagged_templates(session)
        replaced = await quality_signals.replaced_templates(session)
        ids = {question.id for _, question, _, _ in replaced}
        versions = await quality_signals.revisions_of(session, ids)

    found = [
        as_trap(question.text, question.options, stats.flag, topic, template, None)
        for question, stats, topic, template in now
    ]

    for revision, question, topic, template in replaced:
        _, options = replacement(revision, question, versions)
        found.append(
            as_trap(revision.text, revision.options, revision.flag, topic, template, options)
        )

    return [item for item in found if item] + company_questions()


def main() -> None:
    data = json.loads(DATASET.read_text()) if DATASET.exists() else {"items": []}
    known = {item["id"] for item in data["items"]}
    new = {item["id"]: item for item in asyncio.run(flagged()) if item["id"] not in known}

    if not new:
        print(f"No new flagged template questions; {len(known)} in the dataset")

        return

    data |= {"about": ABOUT, "built": datetime.now(UTC).date().isoformat(), "model": "exported"}
    data["items"] += list(new.values())
    DATASET.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(new)} added, {len(data['items'])} in the dataset")


if __name__ == "__main__":
    main()
