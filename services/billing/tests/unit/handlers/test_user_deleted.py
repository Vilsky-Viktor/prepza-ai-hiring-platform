"""Accounts' `user.deleted`: billing deletes its part of the account."""

import asyncio
from datetime import UTC, datetime

from billing.handlers import dispatch, user_deleted

WHEN = datetime(2026, 10, 29, 9, tzinfo=UTC)


def test_a_deleted_account_is_deleted_here(monkeypatch):
    deleted = []

    async def delete_user(user_id):
        deleted.append(user_id)

    monkeypatch.setattr(user_deleted.accounts, "delete_user", delete_user)

    asyncio.run(
        dispatch.handle("user.deleted", {"user_id": "ann", "email": "a@example.com"}, "e1", WHEN)
    )

    assert deleted == ["ann"]
