import uuid

from sqlalchemy import select

from rounds.core.db import Session
from rounds.models.answers import Answer
from rounds.models.outbox import OutboxEvent
from rounds.repositories import sessions
from tests.integration.factories import option_index, topic


def test_an_answer_and_its_event_are_saved_together_and_a_repeat_saves_neither(run):
    async def scenario():
        [row] = await sessions.create_many(
            "ann", uuid.uuid4(), [topic()], 60, company_id=uuid.uuid4()
        )
        question = row.questions[0]
        event = ("answer.recorded", {"question_id": question["id"], "option": "right"})

        def answer():
            return Answer(
                session_id=row.id,
                question_id=uuid.UUID(question["id"]),
                option_index=option_index(question, True),
                correct=True,
                score=100,
            )

        first = await sessions.add_answer(answer(), event)
        again = await sessions.add_answer(answer(), event)

        async with Session() as session:
            saved = list(
                await session.scalars(
                    select(OutboxEvent).where(
                        OutboxEvent.data["question_id"].astext == question["id"]
                    )
                )
            )

        return first, again, len(saved)

    first, again, saved = run(scenario())

    # The repeated answer was refused, and its event rolled back with it.
    assert (first, again, saved) == (True, False, 1)
