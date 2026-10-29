import asyncio

import httpx
from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.config.constants import ACCOUNT_OWNS_SHARED

from accounts.core.db import Session
from accounts.helpers.accounts import candidate_email
from accounts.integrations import services
from accounts.repositories import user_data
from accounts.services.accounts import delete_sign_in
from accounts.services.erasures import erase


async def delete_account(user: User) -> None:
    """Deletes everything about the user, in every service, then their sign-in.

    Companies goes first, by a call: it refuses (409) while the user owns a company others have
    joined, before anything is deleted, and it settles their unfinished invites while rounds
    still has their answers. Then, in one save, accounts' own rows go with the note that runs
    the deletion again after a restore and the `user.deleted` event every other holder deletes
    its part by (services/erasures.py). Each step is safe to repeat and raises on failure, so a
    failed deletion is retried whole; the sign-in, which lets the user retry, goes last.
    """
    email = candidate_email(user)

    try:
        await services.delete_in_companies(user.uid, email)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(status.HTTP_409_CONFLICT, ACCOUNT_OWNS_SHARED) from error

        raise

    await erase(user.uid, email)
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
