import pytest
from fastapi import HTTPException
from sqlalchemy import select, update

from library.constants.events import QUESTION_FIXED
from library.core.db import Session
from library.models.outbox import OutboxEvent
from library.models.sets import Question
from library.repositories import preparations, quality, templates
from library.services import copy_fixes
from tests.integration.factories import COPYABLE, a_company, interview

FIXED = [{"answer": "Right", "correct": True}, {"answer": "Wrong", "correct": False}]


async def first_question(set_id):
    return (await preparations.get_content(set_id)).topics[0].questions[0]


async def fixed_event(question_id) -> dict:
    """The question.fixed event saved with the bank question's fix, as Pub/Sub pushes it back."""
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent.data).where(OutboxEvent.event_type == QUESTION_FIXED)
        )

        return next(row for row in rows if row["question_id"] == str(question_id))


async def notified_companies(question_ids) -> list[str]:
    """The companies told a question in their test was fixed, one per fixed question."""
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent.data).where(
                OutboxEvent.event_type == "notification.requested",
                OutboxEvent.data["kind"].astext == "question_fixed",
            )
        )

        return sorted(row["recipient_id"] for row in rows if row["recipient_id"] in question_ids)


def test_a_fixed_bank_question_fixes_its_unchanged_copies_in_companies_tests(run):
    async def scenario():
        template = await interview("Rigger", template=True, questions=COPYABLE)
        acme = await templates.copy_template(template, a_company("acme-fix"))
        globex = await templates.copy_template(template, a_company("globex-fix"))
        copy = await first_question(acme.id)
        changed = await first_question(globex.id)

        # Globex's copy was fixed on its own already: it keeps its content.
        async with Session() as session:
            await session.execute(
                update(Question).where(Question.id == changed.id).values(text="Globex's own?")
            )
            await session.commit()

        await quality.save_flag(copy.source_question_id, "wrong_key")
        await preparations.replace_question(copy.source_question_id, "Which is right?", FIXED)
        event = await fixed_event(copy.source_question_id)
        await copy_fixes.fix_copies(event)
        # Pushed again, it fixes nothing twice.
        await copy_fixes.fix_copies(event)

        return (
            await first_question(acme.id),
            await first_question(globex.id),
            await notified_companies([a_company("acme-fix"), a_company("globex-fix")]),
        )

    copy, changed, notified = run(scenario())

    assert (copy.text, [option["answer"] for option in copy.options]) == (
        "Which is right?",
        ["Right", "Wrong"],
    )
    assert changed.text == "Globex's own?"
    assert notified == [a_company("acme-fix")]


def test_a_bank_question_rewritten_without_a_flag_leaves_its_copies(run):
    async def scenario():
        template = await interview("Scaffolder", template=True, questions=COPYABLE)
        acme = await templates.copy_template(template, a_company("acme-nofix"))
        copy = await first_question(acme.id)
        await preparations.replace_question(copy.source_question_id, "Reworded?", FIXED)

        return copy, await first_question(acme.id)

    before, after = run(scenario())

    assert after.text == before.text


def test_copies_are_fixed_a_batch_at_a_time_and_a_push_past_its_time_comes_back(run, monkeypatch):
    monkeypatch.setattr(copy_fixes, "COPY_FIX_BATCH", 1)
    monkeypatch.setattr("library.repositories.copy_fixes.COPY_FIX_BATCH", 1)
    monkeypatch.setattr(copy_fixes, "COPY_FIX_SECONDS", -1)

    async def scenario():
        template = await interview("Welder", template=True, questions=COPYABLE)
        first = await templates.copy_template(template, a_company("initech-fix"))
        second = await templates.copy_template(template, a_company("hooli-fix"))
        original = (await first_question(first.id)).source_question_id
        await quality.save_flag(original, "wrong_key")
        await preparations.replace_question(original, "Which is right?", FIXED)
        event = await fixed_event(original)

        with pytest.raises(HTTPException) as busy:
            await copy_fixes.fix_copies(event)

        texts = sorted(
            [(await first_question(first.id)).text, (await first_question(second.id)).text]
        )
        # Pub/Sub pushes it again until it's taken: the copy left is fixed.
        for _ in range(3):
            try:
                await copy_fixes.fix_copies(event)

                break
            except HTTPException:
                continue

        return (
            busy.value.status_code,
            texts,
            [(await first_question(set_id)).text for set_id in (first.id, second.id)],
        )

    status_code, texts, after = run(scenario())

    assert status_code == 503
    assert texts.count("Which is right?") == 1
    assert after == ["Which is right?", "Which is right?"]
