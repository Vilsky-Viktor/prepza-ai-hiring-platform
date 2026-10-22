"""A candidate an ATS's web hook sends is saved at once and invited within HOOK_INVITE_SECONDS,
so the web hook is answered in time; one companies is slow to invite waits for the recovery
job."""

import asyncio
import uuid
from types import SimpleNamespace

from app.services import ats_candidates as flow
from app.storage import ats_candidates


def test_a_slow_companies_leaves_the_candidate_saved_for_the_recovery_job(monkeypatch):
    saved = []
    row = SimpleNamespace(id=uuid.uuid4(), interview_id=uuid.uuid4())

    async def add(*args):
        saved.append(args)

        return row

    async def slow(ids):
        await asyncio.Event().wait()

    monkeypatch.setattr(ats_candidates, "add", add)
    monkeypatch.setattr(flow.companies, "interviews", slow)
    monkeypatch.setattr(flow, "HOOK_INVITE_SECONDS", 0.01)
    link = SimpleNamespace(id=uuid.uuid4(), interview_id=row.interview_id)
    connection = SimpleNamespace(id=uuid.uuid4())

    asyncio.run(flow.arrived(link, connection, "c-1", "ann@example.com", "Ann"))

    assert len(saved) == 1
