import asyncio
import itertools

from firebase_admin import auth as firebase_auth
from prepza_common.auth.auth import claims_language

from accounts.constants.emails import FIREBASE_LOOKUP_LIMIT
from accounts.core.db import Session
from accounts.repositories import emails


async def recipients(user_ids: list[str]) -> list[dict]:
    """Each user's sign-in email, interface language and email preferences; users who are gone,
    disabled or have no email are left out."""
    accounts = []

    for start in range(0, len(user_ids), FIREBASE_LOOKUP_LIMIT):
        chunk = user_ids[start : start + FIREBASE_LOOKUP_LIMIT]
        found = await asyncio.to_thread(
            firebase_auth.get_users, [firebase_auth.UidIdentifier(uid) for uid in chunk]
        )
        accounts += [account for account in found.users if account.email and not account.disabled]

    async with Session() as session:
        preferences = await emails.preferences_of(session, [account.uid for account in accounts])

    return [
        {
            "user_id": account.uid,
            "email": account.email,
            "language": claims_language(account.custom_claims or {}),
            "preferences": preferences[account.uid],
        }
        for account in accounts
    ]


def user_ids_after(after: str, limit: int) -> list[str]:
    """Up to `limit` account ids after `after`, in Firebase's order (by id), which reads them a
    page at a time; its page token is the last id of the page before (blocking: run it in a
    thread)."""
    accounts = firebase_auth.list_users(page_token=after or None).iterate_all()

    return [account.uid for account in itertools.islice(accounts, limit)]
