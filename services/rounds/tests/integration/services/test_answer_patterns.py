import uuid

from rounds.constants.answer_patterns import FOLLOW_UPS, PatternSignal
from rounds.helpers.integrity_report import answer_patterns
from rounds.models.answers import Answer
from rounds.repositories import sessions
from rounds.schemas.library import TopicQuestions
from rounds.services import sections
from tests.integration.factories import created, option_index
from tests.integration.transactions import transaction

HARD, EASY = 0.2, 0.9


def topic(title: str) -> TopicQuestions:
    """Six questions of rising length, so their fitted times differ; the odd ones hard."""
    return TopicQuestions.model_validate(
        {
            "id": str(uuid.uuid4()),
            "preparation_id": str(uuid.uuid4()),
            "title": title,
            "questions": [
                {
                    "id": str(uuid.uuid4()),
                    "text": f"{title} {index}: " + "Which option holds here? " * (1 + 6 * index),
                    "options": [
                        {"answer": "right", "correct": True},
                        {"answer": "wrong", "correct": False},
                    ],
                    "difficulty": HARD if index % 2 else EASY,
                }
                for index in range(6)
            ],
        }
    )


def relayed(row) -> list[Answer]:
    """What relaying to an AI looks like: hard questions right, easy ones wrong, and 24-30 s on
    each whatever its time, the longest the quickest."""
    by_time = sorted(row.questions, key=lambda question: question["seconds"])

    return [
        Answer(
            session_id=row.id,
            question_id=uuid.UUID(question["id"]),
            option_index=option_index(question, question["difficulty"] == HARD),
            correct=question["difficulty"] == HARD,
            score=100 if question["difficulty"] == HARD else 0,
            seconds=30 - position % 7,
        )
        for position, question in enumerate(by_time)
    ]


def test_the_patterns_show_once_every_section_is_finished(run):
    invite_id = uuid.uuid4()

    async def scenario():
        rows = await created(
            "cand", invite_id, [topic("SQL"), topic("APIs")], 60, company_id=uuid.uuid4()
        )
        found = []

        for row in rows:
            for answer in relayed(row):
                await transaction(sessions.add_answer, answer)

        found.append(answer_patterns(await transaction(sessions.list_for_invite, invite_id)))
        await transaction(sections.finish, rows[0].id)
        found.append(answer_patterns(await transaction(sessions.list_for_invite, invite_id)))
        await transaction(sections.finish, rows[1].id)
        found.append(answer_patterns(await transaction(sessions.list_for_invite, invite_id)))

        return rows, found

    rows, (running, half, finished) = run(scenario())

    # Nothing while a section is still going.
    assert running.signals == running.follow_ups == half.signals == half.follow_ups == []
    # The difficulties kept with the questions at the start are what the pattern reads.
    assert {question["difficulty"] for question in rows[0].questions} == {HARD, EASY}
    assert [signal.kind for signal in finished.signals] == [
        PatternSignal.TIMING,
        PatternSignal.PERSON_FIT,
    ]
    assert (finished.signals[1].hard_right, finished.signals[1].easy_wrong) == (6, 6)
    hard = {q["id"] for row in rows for q in row.questions if q["difficulty"] == HARD}
    assert len(finished.follow_ups) == FOLLOW_UPS
    assert {str(f.question_id) for f in finished.follow_ups} <= hard
