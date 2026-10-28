"""A deleted interview's unfinished invites are settled a page at a time, read by key."""

import asyncio
import uuid
from types import SimpleNamespace

from companies.repositories import invites
from companies.services import candidate_billing


def test_unfinished_invites_are_settled_page_by_page(monkeypatch):
    rows = [SimpleNamespace(id=uuid.UUID(int=index)) for index in range(1, 6)]
    asked, settled = [], []

    async def unfinished(interview_id, after, size):
        asked.append(after)
        start = 0 if after is None else rows.index(next(r for r in rows if r.id == after)) + 1

        return rows[start : start + size]

    async def settle_removed(page):
        settled.append(len(page))

    monkeypatch.setattr(candidate_billing, "SETTLE_BATCH", 2)
    monkeypatch.setattr(invites, "unfinished", unfinished)
    monkeypatch.setattr(candidate_billing, "settle_removed", settle_removed)

    asyncio.run(candidate_billing.settle_unfinished(uuid.uuid4()))

    assert settled == [2, 2, 1]
    assert asked == [None, rows[1].id, rows[3].id]
