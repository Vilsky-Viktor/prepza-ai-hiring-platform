from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from library.models.feedback import QuestionRating, QuestionReport, QuestionReporter
from library.models.sets import Question


async def delete_user(session: AsyncSession, user_id: str) -> None:
    """The user's ratings and reports of questions, given as a candidate."""
    for model in (QuestionRating, QuestionReport, QuestionReporter):
        await session.execute(delete(model).where(model.user_id == user_id))


async def export(session: AsyncSession, user_id: str) -> dict:
    votes = await session.execute(
        select(Question.text, QuestionRating.value)
        .join(Question, Question.id == QuestionRating.question_id)
        .where(QuestionRating.user_id == user_id)
    )
    reports = await session.execute(
        select(
            Question.text,
            QuestionReport.reason,
            QuestionReport.comment,
            QuestionReport.created_at,
        )
        .join(Question, Question.id == QuestionReport.question_id)
        .where(QuestionReport.user_id == user_id)
    )

    # Kept after a reported question is replaced, so its current wording is what they're shown.
    reported = await session.scalars(
        select(Question.text)
        .join(QuestionReporter, QuestionReporter.question_id == Question.id)
        .where(QuestionReporter.user_id == user_id)
    )

    return {
        "question_votes": [{"question": text, "vote": value} for text, value in votes],
        "question_reports": [
            {"question": text, "reason": reason, "comment": comment, "at": at}
            for text, reason, comment, at in reports
        ],
        "questions_reported": list(reported),
    }
