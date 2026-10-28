"""An interview's sections carry its company, and so do their answers and signals."""

import uuid

from sqlalchemy import select

from rounds.core.db import Session
from rounds.models.answers import Answer
from rounds.models.signals import Signal
from rounds.repositories import sessions, signals
from tests.integration.factories import MOST_SIGNALS, created, topic
from tests.integration.transactions import transaction


def test_a_sections_answers_and_signals_carry_its_company(run):
    company = uuid.uuid4()

    async def scenario():
        [row] = await created("cand", uuid.uuid4(), [topic()], 60, company_id=company)
        question = row.questions[0]
        await transaction(
            sessions.add_answer,
            Answer(
                session_id=row.id,
                question_id=uuid.UUID(question["id"]),
                option_index=0,
                correct=False,
                score=0,
                seconds=3,
            ),
        )
        await transaction(signals.add_signal, row.id, None, "copy", MOST_SIGNALS)

        async with Session() as session:
            answer = await session.scalar(
                select(Answer.company_id).where(Answer.session_id == row.id)
            )
            signal = await session.scalar(
                select(Signal.company_id).where(Signal.session_id == row.id)
            )

        return row.company_id, answer, signal

    assert run(scenario()) == (company, company, company)
