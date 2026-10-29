import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from library.helpers.quality import difficulty
from library.models.quality import QuestionStats
from library.models.sets import Question


async def for_questions(
    session: AsyncSession, questions: list[Question]
) -> dict[uuid.UUID, float | None]:
    """Each question's difficulty (helpers/quality.py difficulty): from its bank original's
    answers when it's a copy, as they add up across every test that uses it, else its own. One
    query for them all."""
    ids = {question.id for question in questions}
    ids |= {question.source_question_id for question in questions if question.source_question_id}
    rows = await session.scalars(select(QuestionStats).where(QuestionStats.question_id.in_(ids)))
    stats = {row.question_id: row for row in rows}

    return {
        question.id: difficulty(stats.get(question.source_question_id or question.id))
        for question in questions
    }
