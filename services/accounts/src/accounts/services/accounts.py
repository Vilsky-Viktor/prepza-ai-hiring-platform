import asyncio

from firebase_admin import auth as firebase_auth
from prepza_common.auth.user import Language, User
from prepza_common.config.constants import GUEST_UID_PREFIX, LANGUAGE_CLAIM, LEGAL_VERSIONS
from prepza_common.events.analytics import track

from accounts.core.db import Session
from accounts.integrations.billing import remember_currency
from accounts.repositories import legal


def delete_sign_in(user_id: str) -> None:
    """Revokes the account's sign-ins, then deletes it: its ID tokens are refused at once for
    any change (auth.py checks revocation on writes), not only once they expire."""
    try:
        firebase_auth.revoke_refresh_tokens(user_id)
        firebase_auth.delete_user(user_id)
    except firebase_auth.UserNotFoundError:
        pass


async def account_by_email(email: str) -> firebase_auth.UserRecord | None:
    """The account signed in with the address, whatever its case; None when there's none, or the
    text couldn't be an address."""
    try:
        return await asyncio.to_thread(firebase_auth.get_user_by_email, email.strip().lower())
    except (firebase_auth.UserNotFoundError, ValueError):
        return None


async def account_by_id(user_id: str) -> firebase_auth.UserRecord | None:
    """The account with that id; None when there's none, or the id couldn't be one."""
    try:
        return await asyncio.to_thread(firebase_auth.get_user, user_id)
    except (firebase_auth.UserNotFoundError, ValueError):
        return None


async def set_language(user: User, language: Language, country: str | None = None) -> None:
    """Stored on the sign-in, so every service reads it from the user's next ID token. A new
    account sets it on its first sign-in (the frontend does), which counts as signing up; it
    then sees prices in its `country`'s currency."""
    record = await asyncio.to_thread(firebase_auth.get_user, user.uid)
    await asyncio.to_thread(
        firebase_auth.set_custom_user_claims, user.uid, {LANGUAGE_CLAIM: language}
    )

    if LANGUAGE_CLAIM not in (record.custom_claims or {}):
        # Signing in the first time accepts the terms (the sign-in shows them).
        async with Session.begin() as session:
            await legal.accept_terms(session, user.uid, LEGAL_VERSIONS["terms"])

        # A company's guest candidate has no account of their own: not a sign-up.
        if not user.uid.startswith(GUEST_UID_PREFIX):
            await track("signed_up", user_id=user.uid, language=language)
            await remember_currency(user.uid, country)
