"""The admin zone's stats from the sign-in accounts: they live in Firebase only."""

import asyncio
from datetime import UTC, datetime

from firebase_admin import auth as firebase_auth
from testee_common.config.constants import GUEST_UID_PREFIX
from testee_common.db.stats import period_range


def created(period: str | None) -> int:
    """Accounts made all time or in `period` (a year or a month), read page by page; a company's
    guest candidates have none of their own."""
    bounds = period_range(period) if period else None
    count = 0

    for account in firebase_auth.list_users().iterate_all():
        if account.uid.startswith(GUEST_UID_PREFIX):
            continue

        made = datetime.fromtimestamp(account.user_metadata.creation_timestamp / 1000, UTC)

        if bounds is None or bounds[0] <= made < bounds[1]:
            count += 1

    return count


async def stats(period: str | None) -> dict[str, int]:
    return {"users": await asyncio.to_thread(created, period)}
