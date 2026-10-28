from sqlalchemy import update

from library.constants.code import TEXT_FENCE
from library.core.db import Session
from library.models.sets import Question
from library.repositories import code
from tests.integration.factories import interview, question_ids
from tests.integration.transactions import transaction

UNTAGGED = "What does it print?\n```\nprint(1)\n```"
# A question already tagged, with text after its example: its closing fence is followed by a
# new line too, but it isn't an example without a language.
TAGGED = "What does it print?\n```python\nprint(1)\n```\nPick one."
UNTAGGED_THEN_TEXT = "Which rows?\n```\nSELECT 1\n```\nPick one."
PLAIN = "What is a closure?"


async def with_texts(*texts):
    ids = await question_ids(await interview("Code", questions=len(texts)))

    async with Session() as session:
        for question_id, body in zip(ids, texts, strict=True):
            await session.execute(
                update(Question).where(Question.id == question_id).values(text=body)
            )

        await session.commit()

    return ids


async def texts_of(ids):
    async with Session() as session:
        rows = await session.execute(Question.__table__.select().where(Question.id.in_(ids)))

        return {row.id: row.text for row in rows}


def test_only_examples_without_a_language_are_listed_and_tagged_once(run):
    async def scenario():
        ids = await with_texts(UNTAGGED, TAGGED, UNTAGGED_THEN_TEXT, PLAIN)
        listed = {question_id for question_id, _ in await transaction(code.untagged, 100)} & set(
            ids
        )
        await transaction(code.tag, {ids[0]: "python", ids[2]: "sql"})
        # Tagging again changes nothing: the question no longer counts as untagged.
        await transaction(code.tag, {ids[0]: "bash", ids[1]: "bash"})
        left = {question_id for question_id, _ in await transaction(code.untagged, 100)} & set(ids)

        return ids, listed, left, await texts_of(ids)

    ids, listed, left, texts = run(scenario())

    assert listed == {ids[0], ids[2]}
    assert left == set()
    assert [texts[question_id] for question_id in ids] == [
        "What does it print?\n```python\nprint(1)\n```",
        TAGGED,
        "Which rows?\n```sql\nSELECT 1\n```\nPick one.",
        PLAIN,
    ]


def test_examples_tagged_text_are_listed_in_pages_and_retagged_once(run):
    files = "Which runs?\n```text\npackage.json\n{}\n```"
    rows = "Which rows?\n```text\nid | name\n```"

    async def scenario():
        ids = sorted(await with_texts(files, rows, TAGGED, UNTAGGED))
        mine = set(ids)
        first = [i for i, _ in await transaction(code.untagged, 100, TEXT_FENCE) if i in mine]
        after = [
            i for i, _ in await transaction(code.untagged, 100, TEXT_FENCE, first[0]) if i in mine
        ]
        texts = await texts_of(ids)
        target = next(i for i in ids if texts[i] == files)
        await transaction(code.tag, {target: "json"}, TEXT_FENCE)
        # The untagged one's fence is never touched by a "text" re-tag.
        untagged = next(i for i in ids if texts[i] == UNTAGGED)
        await transaction(code.tag, {untagged: "bash"}, TEXT_FENCE)
        left = [i for i, _ in await transaction(code.untagged, 100, TEXT_FENCE) if i in mine]

        return first, after, left, await texts_of(ids)

    first, after, left, texts = run(scenario())

    assert first == sorted(first) and len(first) == 2
    assert after == first[1:]
    assert sorted(texts.values()) == sorted(
        ["Which runs?\n```json\npackage.json\n{}\n```", rows, TAGGED, UNTAGGED]
    )
    assert len(left) == 1 and texts[left[0]] == rows
