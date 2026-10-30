"""The shared question bank: which companies' questions join it, what takes them out, and how
new interviews reuse them (docs/generation.md, The question bank)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import text

from library.constants.quality import QualityFlag
from library.core.db import Session
from library.integrations import generation
from library.repositories import preparations, quality, reuse
from library.services import bank as bank_service
from library.services import quality as quality_service
from library.services import question_feedback
from tests.integration.bank_factories import (
    bank_rows,
    check,
    prove,
    reused_interview,
    shared_interview,
)
from tests.integration.factories import a_company, copy_of, direction, interview, question_ids
from tests.integration.transactions import transaction

NOW = datetime(2026, 10, 30, tzinfo=UTC)


async def offered(company: str, embedding=None) -> set:
    found = await transaction(
        reuse.find, embedding or direction(1.0), "medium", "en", 50, uuid.UUID(company)
    )

    return {question_id for question_id, _, _ in found}


async def candidate_ids() -> set:
    return {c.question_id for c in await bank_service.candidates(100, None)}


def test_only_proven_questions_that_passed_the_filter_join_without_their_company(run):
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        set_id = await interview(
            f"Join {uuid.uuid4()}", owner=company, questions=4, embedding=direction(1.0)
        )
        passed, failed, unproven, flagged = await question_ids(set_id)
        await prove([passed, failed, flagged])
        await prove([unproven], answers=29)
        await transaction(quality.save_flag, flagged, QualityFlag.REWRITE)
        offered_before = await candidate_ids()
        await check([passed, flagged, unproven])
        await check([failed], passed=False)
        joined = await bank_rows([passed, failed, unproven, flagged])

        async with Session() as session:
            columns = await session.scalars(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'bank_questions'"
                )
            )
            column_names = set(columns)

        return (
            (passed, failed, unproven, flagged),
            offered_before,
            joined,
            column_names,
            (await candidate_ids()),
        )

    (passed, failed, unproven, flagged), before, joined, columns, after = run(scenario())

    # Proven and flagged ones are offered to the filter; a question answered too few times isn't.
    assert {passed, failed, flagged} <= before and unproven not in before
    assert set(joined) == {passed}
    assert "company_id" not in columns
    # Checked as they read now, none is offered again.
    assert not {passed, failed, flagged} & after


def test_a_changed_question_is_checked_again_and_copies_never_join(run):
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        set_id = await interview(f"Change {uuid.uuid4()}", owner=company, questions=1)
        [question_id] = await question_ids(set_id)
        await prove([question_id])
        await check([question_id], passed=False)

        async with Session.begin() as session:
            await session.execute(
                text("UPDATE questions SET text = 'Reworded?' WHERE id = :id"), {"id": question_id}
            )

        template = await interview(f"Template {uuid.uuid4()}", template=True, questions=40)
        copy = await copy_of(template, company)
        copies = await question_ids(copy.id)
        await prove(copies)

        return question_id, copies, await candidate_ids()

    question_id, copies, offered_now = run(scenario())

    assert question_id in offered_now
    assert not set(copies) & offered_now


def test_a_flag_or_report_takes_a_bank_question_out_for_good(run, monkeypatch):
    """On the source or on another company's copy of it: out of the bank for everyone, the copy
    stays in that company's interview, and the source never joins again."""
    company, other = a_company(str(uuid.uuid4())), a_company(str(uuid.uuid4()))
    sent = []

    async def fake_verify(question_id, flag):
        sent.append(question_id)

    monkeypatch.setattr(generation, "verify_question", fake_verify)

    async def scenario():
        _, (flagged, reported, copied) = await shared_interview(company, questions=3)
        bank = await bank_rows([flagged, reported, copied])
        new = await reused_interview(other, [bank[copied]])
        [copy_id] = await question_ids(new)
        await quality_service.mark_wrong(flagged)
        await question_feedback.report(reported, "ann", "unclear", "")
        await quality_service.mark_wrong(copy_id)
        await bank_service.sweep()
        await check([flagged, reported, copied])

        return copy_id, await bank_rows([flagged, reported, copied]), await question_ids(new)

    copy_id, left, still = run(scenario())

    assert left == {}
    assert still == [copy_id]


def test_a_new_interview_reuses_other_companies_bank_questions_never_its_own(run):
    """Templates' generations (no company) and practice never get them; the company's own
    question is never offered back to it as new."""
    company, other = a_company(str(uuid.uuid4())), a_company(str(uuid.uuid4()))
    embedding = direction(0.0, 1.0)

    async def scenario():
        _, ids = await shared_interview(company, questions=2, embedding=embedding)
        bank = await bank_rows(ids)
        template = await transaction(reuse.find, embedding, "medium", "en", 50, None)
        new = await reused_interview(other, list(bank.values()))
        content = await transaction(preparations.get_content, new)
        marks = [
            (q.source_question_id, q.bank_question_id)
            for topic in content.topics
            for q in topic.questions
        ]

        return (
            set(bank.values()),
            await offered(company, embedding),
            await offered(other, embedding),
            {question_id for question_id, _, _ in template},
            marks,
        )

    bank_ids, own, others, template, marks = run(scenario())

    assert not bank_ids & own
    assert bank_ids <= others
    assert not bank_ids & template
    # The copies are marked as the bank questions', without a template original.
    assert sorted(marks, key=str) == sorted(((None, b) for b in bank_ids), key=str)


def test_the_daily_sweep_takes_out_what_raced_a_flag(run):
    """A question flagged in a transaction that didn't see it join: the sweep takes it out and
    bars it."""
    company = a_company(str(uuid.uuid4()))

    async def scenario():
        _, [question_id] = await shared_interview(company, questions=1)
        await transaction(quality.save_flag, question_id, QualityFlag.REWRITE)
        before = await bank_rows([question_id])
        await bank_service.sweep()

        async with Session() as session:
            barred = await session.scalar(
                text("SELECT barred FROM bank_checks WHERE question_id = :id"), {"id": question_id}
            )

        return before, await bank_rows([question_id]), barred

    before, after, barred = run(scenario())

    assert len(before) == 1
    assert after == {}
    assert barred is True
