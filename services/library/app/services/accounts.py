import asyncio

import httpx
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from prepza_common.analytics import track
from prepza_common.constants import (
    ACCOUNT_OWNS_SHARED,
    GUEST_UID_PREFIX,
    LANGUAGE_CLAIM,
    LEGAL_VERSIONS,
)
from prepza_common.user import Language, User

from app.helpers.accounts import candidate_email
from app.integrations import accounts as services
from app.integrations.billing import remember_currency
from app.storage import accounts, erasures, legal


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
        await legal.accept_terms(user.uid, LEGAL_VERSIONS["terms"])

        # A company's guest candidate has no account of their own: not a sign-up.
        if not user.uid.startswith(GUEST_UID_PREFIX):
            await track("signed_up", user_id=user.uid, language=language)
            await remember_currency(user.uid, country)


async def delete_account(user: User) -> None:
    """Deletes everything about the user, in every service, then their sign-in.

    Each step is safe to repeat and raises on failure, so a failed deletion is retried whole and
    the sign-in, which lets the user retry, goes last. Companies goes first: it refuses (409)
    while the user owns a company others have joined, before any service deleted anything. The
    other services then delete at once, so the whole request takes two calls' time, not eight,
    within library's own request timeout.
    """
    first, *others = services.services()
    email = candidate_email(user)

    try:
        await services.delete_user(first, user.uid, email)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, ACCOUNT_OWNS_SHARED) from error

        raise

    # Every one is awaited, failed or not, so none is left running after the answer.
    results = await asyncio.gather(
        *(services.delete_user(service, user.uid, email) for service in others),
        return_exceptions=True,
    )
    failed = [result for result in results if isinstance(result, BaseException)]

    if failed:
        raise failed[0]

    await accounts.delete_user(user.uid)
    # Run again after a restore from a backup (services/erasures.py).
    await erasures.record(user.uid, candidate_email(user))
    await asyncio.to_thread(delete_sign_in, user.uid)


async def export_account(user: User) -> dict:
    exports = await asyncio.gather(
        *(
            services.export_user(name, user.uid, candidate_email(user))
            for name in services.services()
        )
    )

    return {
        "account": {
            "id": user.uid,
            "email": user.email,
            "name": user.name,
            "language": user.language,
        },
        "library": await accounts.export(user.uid),
        **dict(zip(services.services(), exports, strict=True)),
    }
