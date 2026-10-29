import random

from prepza_common.ai.multi_answer import is_multi

from rounds.schemas.rounds import NextQuestion


def next_question(row) -> NextQuestion | None:
    """The first question of a session without an answer, numbered from 1."""
    answered = {str(answer.question_id) for answer in row.answers}

    for number, question in enumerate(row.questions, start=1):
        if question["id"] not in answered:
            return NextQuestion(
                question_id=question["id"],
                number=number,
                text=question["text"],
                options=[option["answer"] for option in question["options"]],
                multi=is_multi(question["options"]),
                seconds=question.get("seconds"),
            )

    return None


def find_question(row, question_id: str) -> dict | None:
    return next((q for q in row.questions if q["id"] == question_id), None)


def correct_indexes(question: dict) -> list[int]:
    """Every right option's place; one for a single-answer question."""
    return [i for i, option in enumerate(question["options"]) if option["correct"]]


def shuffled(questions: list[dict]) -> list[dict]:
    """Each candidate gets their own question and option order, so answers can't be passed on."""
    random.shuffle(questions)

    for question in questions:
        random.shuffle(question["options"])

    return questions
