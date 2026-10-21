from sqlalchemy import select, update

from app.models.outbox import OutboxEvent
from app.models.sets import Question
from app.storage import preparations, quality, templates
from app.storage.db import Session
from tests.integration.factories import COPYABLE, a_company, interview

FIXED = [{"answer": "Right", "correct": True}, {"answer": "Wrong", "correct": False}]


async def first_question(set_id):
    return (await preparations.get_content(set_id)).topics[0].questions[0]


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
