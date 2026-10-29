import uuid

from library.constants.quality import MIN_ANSWERS
from library.repositories import answer_stats, difficulty, preparations
from tests.integration.factories import COPYABLE, a_company, copy_of, interview
from tests.integration.transactions import transaction


async def answer(question, right: int, total: int) -> None:
    """`total` answers to the question, `right` of them right."""
    for index in range(total):
        await transaction(
            answer_stats.record_answer,
            str(uuid.uuid4()),
            question.id,
            question.text,
            ["right" if index < right else "wrong"],
            1.0 if index < right else 0.0,
        )


async def questions(set_id) -> list:
    content = await transaction(preparations.get_content, set_id)

    return [question for topic in content.topics for question in topic.questions]


def test_a_question_has_a_difficulty_once_it_has_enough_answers(run):
    async def scenario():
        set_id = await interview(f"Difficulty {uuid.uuid4().hex[:8]}", questions=3)
        known, short, fresh = await questions(set_id)
        await answer(known, 12, MIN_ANSWERS)
        await answer(short, 5, MIN_ANSWERS - 1)

        return await transaction(difficulty.for_questions, [known, short, fresh]), known, short

    found, known, short = run(scenario())

    assert found[known.id] == 0.4
    # Too few answers to say anything, or none.
    assert list(found.values()).count(None) == 2
    assert found[short.id] is None


def test_a_copied_bank_question_takes_its_originals_difficulty(run):
    async def scenario():
        template = await interview(
            f"Bank {uuid.uuid4().hex[:8]}", template=True, questions=COPYABLE
        )
        copy = await copy_of(template, a_company(f"difficulty-{uuid.uuid4()}"))
        copied = (await questions(copy.id))[0]
        original = next(q for q in await questions(template) if q.id == copied.source_question_id)
        # The bank original's answers add up across every test that uses it.
        await answer(original, 24, MIN_ANSWERS)

        return await transaction(difficulty.for_questions, [copied]), copied

    found, copied = run(scenario())

    assert found[copied.id] == 0.8
