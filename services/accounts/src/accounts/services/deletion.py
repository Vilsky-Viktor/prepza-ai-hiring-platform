import asyncio

import httpx
from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.config.constants import ACCOUNT_OWNS_SHARED

from accounts.core.db import Session
from accounts.helpers.accounts import candidate_email
from accounts.integrations import services
from accounts.repositories import erasures, user_data
from accounts.services.accounts import delete_sign_in


async def delete_account(user: User) -> None:
    """Deletes everything about the user, in every service, then their sign-in.

    Each step is safe to repeat and raises on failure, so a failed deletion is retried whole and
    the sign-in, which lets the user retry, goes last. Companies goes first: it refuses (409)
    while the user owns a company others have joined, before any service deleted anything. The
    other services then delete at once, so the whole request takes two calls' time, not nine,
    within accounts' own request timeout.
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

    # One save: accounts' rows go with the note that runs the deletion again after a restore
    # from a backup (services/erasures.py), so neither is kept without the other.
    async with Session.begin() as session:
        await user_data.delete_user(session, user.uid)
        await erasures.record(session, user.uid, email)

    await asyncio.to_thread(delete_sign_in, user.uid)


async def export_account(user: User) -> dict:
    exports = await asyncio.gather(
        *(
            services.export_user(name, user.uid, candidate_email(user))
            for name in services.services()
        )
    )

    async with Session() as session:
        own = await user_data.export(session, user.uid)

    return {
        "account": {
            "id": user.uid,
            "email": user.email,
            "name": user.name,
            "language": user.language,
        },
        "accounts": own,
        **dict(zip(services.services(), exports, strict=True)),
    }
