from prepza_common.ai.multi_answer import is_multi

from library.models.sets import Question
from library.repositories import feedback
from library.schemas.preparations import QuestionText


async def question_texts(questions: list[Question]) -> list[QuestionText]:
    """Questions with their options and feedback counts."""
    stats = await feedback.question_stats([question.id for question in questions])

    return [
        QuestionText(
            id=question.id,
            text=question.text,
            options=question.options,
            multi=is_multi(question.options),
            **stats.get(question.id, {}),
        )
        for question in questions
    ]
