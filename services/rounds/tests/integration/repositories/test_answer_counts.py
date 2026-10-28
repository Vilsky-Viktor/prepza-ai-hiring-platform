import uuid

from rounds.models.answers import Answer
from rounds.repositories import answer_counts, sessions
from tests.integration.factories import created, option_index, topic
from tests.integration.transactions import transaction


def answer(row, index, timed_out):
    question = row.questions[index]

    return Answer(
        session_id=row.id,
        question_id=uuid.UUID(question["id"]),
        option_index=None if timed_out else option_index(question, True),
        timed_out=timed_out,
        correct=not timed_out,
        score=0 if timed_out else 100,
        seconds=30,
    )


def test_answers_are_counted_per_interview_with_timeouts_and_without_previews(run):
    async def scenario():
        shared = topic()
        [first] = await created("ann", uuid.uuid4(), [shared], 30, company_id=uuid.uuid4())
        [second] = await created("bob", uuid.uuid4(), [shared], 30, company_id=uuid.uuid4())
        [preview] = await created(
            "cto", uuid.uuid4(), [shared], 30, preview=True, company_id=uuid.uuid4()
        )
        other = topic()
        await created("dan", uuid.uuid4(), [other], 30, company_id=uuid.uuid4())

        for row, index, timed_out in (
            (first, 0, True),
            (first, 1, False),
            (second, 0, False),
            (preview, 0, True),
        ):
            await transaction(sessions.add_answer, answer(row, index, timed_out))

        found = await transaction(
            answer_counts.for_sets, [shared.preparation_id, other.preparation_id]
        )

        return found, shared.preparation_id

    found, shared_id = run(scenario())

    # One of the three candidates' answers timed out; the preview's doesn't count, and the
    # other interview has no answers yet.
    assert found == {shared_id: [1, 3]}
