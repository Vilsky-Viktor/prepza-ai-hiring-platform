"""Questions in the shared bank for the tests: a company's interview whose questions are proven
(answered MIN_ANSWERS times) and passed the filter, as generation's daily job leaves them."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from testee_common.ai.sets import PreparationIn

from library.constants.quality import MIN_ANSWERS
from library.core.db import Session
from library.schemas.bank import BankCheckIn
from library.services import bank as bank_service
from library.services import sets as set_service
from tests.integration.factories import direction, interview, question_ids

NOW = datetime(2026, 10, 30, tzinfo=UTC)


async def prove(ids, answers=MIN_ANSWERS):
    """The questions answered `answers` times, unflagged."""
    async with Session.begin() as session:
        await session.execute(
            text(
                "INSERT INTO question_stats (question_id, answers, correct, option_picks, updated_at) "
                "VALUES (:id, :answers, 0, '{}', now()) "
                "ON CONFLICT (question_id) DO UPDATE SET answers = excluded.answers"
            ),
            [{"id": question_id, "answers": answers} for question_id in ids],
        )


async def wording(question_id) -> str:
    async with Session() as session:
        return await session.scalar(
            text("SELECT text FROM questions WHERE id = :id"), {"id": question_id}
        )


async def check(ids, passed=True):
    """The filter's verdicts on the questions as they read now, as generation sends them."""
    checks = [
        BankCheckIn(question_id=question_id, text=await wording(question_id), passed=passed)
        for question_id in ids
    ]
    await bank_service.save_checks(checks)


async def shared_interview(company: str, questions=2, embedding=None):
    """A company's interview whose questions all joined the bank: (set id, question ids)."""
    set_id = await interview(
        f"Shared {uuid.uuid4()}",
        owner=company,
        questions=questions,
        embedding=embedding or direction(1.0),
    )
    ids = await question_ids(set_id)
    await prove(ids)
    await check(ids)

    return set_id, ids


async def bank_rows(ids) -> dict:
    """The bank copies of these questions: {source id: bank id}."""
    async with Session() as session:
        rows = await session.execute(
            text(
                "SELECT source_question_id, id FROM bank_questions WHERE source_question_id = ANY(:ids)"
            ),
            {"ids": list(ids)},
        )

        return dict(rows.all())


async def bank_by_id(bank_ids) -> dict:
    """{bank id: (source id or None, text)} of these bank questions, as they are now."""
    async with Session() as session:
        rows = await session.execute(
            text("SELECT id, source_question_id, text FROM bank_questions WHERE id = ANY(:ids)"),
            {"ids": list(bank_ids)},
        )

        return {bank_id: (source, wording) for bank_id, source, wording in rows}


def privacy(
    company: str, set_id, keep_private: bool, at=NOW, interview_id=None, generation_id=None
):
    return {
        "interview_id": str(interview_id or uuid.uuid4()),
        "company_id": company,
        "set_id": str(set_id) if set_id else None,
        "generation_id": str(generation_id) if generation_id else None,
        "keep_private": keep_private,
        "changed_at": at.isoformat(),
    }


async def reused_interview(company: str, bank_ids: list):
    """A new interview of `company` that reused these bank questions, as generation saves one."""
    async with Session() as session:
        rows = await session.execute(
            text("SELECT id, text, options FROM bank_questions WHERE id = ANY(:ids)"),
            {"ids": bank_ids},
        )
        found = rows.all()

    payload = PreparationIn.model_validate(
        {
            "generation_id": str(uuid.uuid4()),
            "owner_uid": company,
            "source_text": "job text",
            "title": "Reused",
            "level": "medium",
            "language": "en",
            "requirements": [],
            "topics": [
                {
                    "title": "Topic",
                    "subtopics": [],
                    "questions": [
                        {"text": wording, "options": options, "source_id": str(bank_id)}
                        for bank_id, wording, options in found
                    ],
                }
            ],
        }
    )

    return await set_service.create_interview(payload)
