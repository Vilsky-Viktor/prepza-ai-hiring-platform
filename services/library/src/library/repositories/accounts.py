from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from library.models.emails import EmailConsent, EmailPreferences
from library.models.feedback import QuestionRating, QuestionReport, QuestionReporter
from library.models.legal import TermsAcceptance
from library.models.sets import Question
from library.repositories import emails, legal


async def delete_user(session: AsyncSession, user_id: str) -> None:
    """The user's ratings and reports of questions, given as a candidate, their email
    preferences with the consent log, and the terms they accepted."""
    models = (
        QuestionRating,
        QuestionReport,
        QuestionReporter,
        EmailPreferences,
        EmailConsent,
        TermsAcceptance,
    )

    for model in models:
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

    return {
        "question_votes": [{"question": text, "vote": value} for text, value in votes],
        "question_reports": [
            {"question": text, "reason": reason, "comment": comment, "at": at}
            for text, reason, comment, at in reports
        ],
        "email_preferences": await emails.preferences(session, user_id),
        "email_consents": await emails.consents(session, user_id),
        "terms_accepted": await legal.accepted_terms(session, user_id),
    }
