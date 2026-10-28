import asyncio

import httpx
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from prepza_common.auth.user import User
from prepza_common.config.constants import ACCOUNT_OWNS_SHARED

from library.core.db import Session
from library.helpers.accounts import candidate_email
from library.integrations import accounts as services
from library.repositories import accounts, erasures


def delete_sign_in(user_id: str) -> None:
    """Revokes the account's sign-ins, then deletes it: its ID tokens are refused at once for
    any change (auth.py checks revocation on writes), not only once they expire."""
    try:
        firebase_auth.revoke_refresh_tokens(user_id)
        firebase_auth.delete_user(user_id)
    except firebase_auth.UserNotFoundError:
        pass


async def delete_account(user: User) -> None:
    """Deletes everything about the user, in every service, then their sign-in.

    Each step is safe to repeat and raises on failure, so a failed deletion is retried whole and
    the sign-in, which lets the user retry, goes last. Companies goes first: it refuses (409)
    while the user owns a company others have joined, before any service deleted anything. The
    other services then delete at once, so the whole request takes two calls' time, not nine,
    within library's own request timeout. Accounts deletes the email settings and accepted terms.
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

    # One save: library's rows go with the note that runs the deletion again after a restore
    # from a backup (services/erasures.py), so neither is kept without the other.
    async with Session.begin() as session:
        await accounts.delete_user(session, user.uid)
        await erasures.record(session, user.uid, email)

    await asyncio.to_thread(delete_sign_in, user.uid)


async def delete_data(user_id: str) -> None:
    """What library keeps under the user's id (accounts.delete_user), in one save."""
    async with Session.begin() as session:
        await accounts.delete_user(session, user_id)


async def export_account(user: User) -> dict:
    exports = await asyncio.gather(
        *(
            services.export_user(name, user.uid, candidate_email(user))
            for name in services.services()
        )
    )

    async with Session() as session:
        library = await accounts.export(session, user.uid)

    return {
        "account": {
            "id": user.uid,
            "email": user.email,
            "name": user.name,
            "language": user.language,
        },
        "library": library,
        **dict(zip(services.services(), exports, strict=True)),
    }
