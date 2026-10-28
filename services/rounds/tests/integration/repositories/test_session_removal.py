"""A deleted interview's sessions go a batch at a time, with their answers and signals."""

import uuid

from sqlalchemy import func, select

from rounds.core.db import Session as Db
from rounds.models.sessions import Session
from rounds.repositories import sessions
from tests.integration.factories import created, topic


def on(interview_set_id: uuid.UUID):
    """A topic of that interview."""
    return topic().model_copy(update={"preparation_id": interview_set_id})


async def count(interview_set_id) -> int:
    async with Db() as session:
        return await session.scalar(
            select(func.count()).where(Session.interview_set_id == interview_set_id)
        )


def test_an_interviews_sessions_go_in_batches_and_others_stay(run, monkeypatch):
    monkeypatch.setattr(sessions, "SESSION_DELETE_BATCH", 1)
    deleted, kept = uuid.uuid4(), uuid.uuid4()

    async def scenario():
        for user in ("cand-a", "cand-b", "cand-c"):
            await created(user, uuid.uuid4(), [on(deleted)], 30, company_id=deleted)

        await created("cand-d", uuid.uuid4(), [on(kept)], 30, company_id=kept)
        await sessions.remove_for_interview(Db, deleted)
        # Again, as a retried deletion would: nothing left to delete.
        await sessions.remove_for_interview(Db, deleted)
        left = (await count(deleted), await count(kept))
        await sessions.remove_for_interview(Db, kept)

        return left

    assert run(scenario()) == (0, 1)
