"""What the assistant's get_updates reads (/internal/questions/updates), against the real
database: when a question was newly flagged, and which flagged questions were fixed, for the
given companies' interviews only."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.models.quality import QuestionRevision, QuestionStats
from app.storage import preparations, quality, question_updates
from app.storage.db import Session
from tests.integration.factories import interview

NEW = [{"answer": "Yes", "correct": True}, {"answer": "No", "correct": False}]


def company():
    return str(uuid.uuid4())


async def questions(owner, title, count=2, template=False):
    created = await interview(title, owner=owner, questions=count, template=template)

    return (await preparations.get_content(created)).topics[0].questions


async def raised_at(question_id):
    async with Session() as session:
        return await session.scalar(
            select(QuestionStats.flag_raised_at).where(QuestionStats.question_id == question_id)
        )


async def revisions(question_id):
    async with Session() as session:
        return list(
            await session.scalars(
                select(QuestionRevision.fixed).where(QuestionRevision.question_id == question_id)
            )
        )


def window():
    now = datetime.now(UTC)

    return now - timedelta(hours=1), now + timedelta(hours=1)


def test_a_new_flag_is_raised_once_and_a_changed_flag_keeps_when(run):
    async def scenario():
        [question] = await questions(company(), f"Raised {uuid.uuid4()}", count=1)
        before = await raised_at(question.id)
        assert await quality.change_flag(question.id, None, "rewrite")
        first = await raised_at(question.id)
        assert await quality.change_flag(question.id, "rewrite", "wrong_key")

        return before, first, await raised_at(question.id)

    before, first, after = run(scenario())

    assert before is None
    assert first is not None
    assert after == first


def test_replacing_a_flagged_question_keeps_it_as_fixed_an_unflagged_one_not(run):
    async def scenario():
        flagged, edited = await questions(company(), f"Fixed {uuid.uuid4()}")
        await quality.change_flag(flagged.id, None, "rewrite")
        await preparations.replace_question(flagged.id, "Clearer?", NEW)
        await preparations.replace_question(edited.id, "Edited?", NEW)

        return await revisions(flagged.id), await revisions(edited.id)

    assert run(scenario()) == ([True], [False])


def test_updates_are_the_given_companies_flagged_and_fixed_questions_in_the_window(run):
    mine, other = company(), company()
    title = f"Updates {uuid.uuid4()}"

    async def scenario():
        flagged, fixed, edited, old = await questions(mine, title, count=4)
        [others] = await questions(other, f"Other {uuid.uuid4()}", count=1)
        [bank] = await questions("superadmin", f"Template {uuid.uuid4()}", 1, template=True)

        for question in (flagged, fixed, old, others, bank):
            await quality.change_flag(question.id, None, "rewrite")

        await preparations.replace_question(fixed.id, "Clearer?", NEW)
        await preparations.replace_question(edited.id, "Edited?", NEW)
        # Flagged and fixed two days ago, before the window.
        await preparations.replace_question(old.id, "Older fix?", NEW)
        await quality.change_flag(old.id, None, "rewrite")
        long_ago = datetime.now(UTC) - timedelta(days=2)

        async with Session() as session:
            await session.execute(
                update(QuestionStats)
                .where(QuestionStats.question_id == old.id)
                .values(flag_raised_at=long_ago)
            )
            await session.execute(
                update(QuestionRevision)
                .where(QuestionRevision.question_id == old.id)
                .values(replaced_at=long_ago)
            )
            await session.commit()

        since, until = window()
        found = await question_updates.between([mine], since, until, 50)
        everyone = await question_updates.between([mine, other], since, until, 50)
        later = await question_updates.between([mine], until, until + timedelta(hours=1), 50)
        one_each = await question_updates.between([mine, other], since, until, 1)
        counts = await question_updates.counts([mine, other], since, until)

        return found, everyone, later, one_each, counts

    found, everyone, later, one_each, counts = run(scenario())

    kinds = sorted((kind, owner, interview_title) for kind, _, owner, interview_title, _ in found)
    assert kinds == [
        ("question_fixed", mine, title),
        ("question_flagged", mine, title),
    ]
    assert {topic for *_, topic in found} == {"Python"}
    assert sorted(owner for _, _, owner, _, _ in everyone) == sorted([mine, mine, other])
    assert later == []
    # The newest of each kind listed; every one counted.
    assert sorted(kind for kind, *_ in one_each) == ["question_fixed", "question_flagged"]
    assert counts == {"question_flagged": 2, "question_fixed": 1}
