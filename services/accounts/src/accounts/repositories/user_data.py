from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from accounts.models.emails import EmailConsent, EmailPreferences
from accounts.models.legal import TermsAcceptance
from accounts.repositories import emails, legal


async def delete_user(session: AsyncSession, user_id: str) -> None:
    """The user's email preferences with the consent log, and the terms they accepted."""
    for model in (EmailPreferences, EmailConsent, TermsAcceptance):
        await session.execute(delete(model).where(model.user_id == user_id))


async def export(session: AsyncSession, user_id: str) -> dict:
    return {
        "email_preferences": await emails.preferences(session, user_id),
        "email_consents": await emails.consents(session, user_id),
        "terms_accepted": await legal.accepted_terms(session, user_id),
    }
