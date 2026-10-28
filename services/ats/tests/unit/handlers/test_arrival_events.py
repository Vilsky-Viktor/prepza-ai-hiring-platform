"""An ATS's web hook is answered once its candidate is saved: inviting them runs from the
ats.candidate_arrived event, once per candidate."""

import asyncio
import uuid
from types import SimpleNamespace

from ats.handlers.dispatch import handle
from ats.repositories import ats_candidates
from ats.services import ats_candidates as flow


def test_the_web_hook_saves_and_publishes_but_invites_no_one(monkeypatch):
    done = []

    async def add(*args):
        done.append("saved")

    async def flush():
        done.append("published")

    async def interviews(ids):
        raise AssertionError("asked companies before the answer")

    monkeypatch.setattr(ats_candidates, "add", add)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", flush)
    monkeypatch.setattr(flow.companies, "interviews", interviews)
    link = SimpleNamespace(id=uuid.uuid4(), interview_id=uuid.uuid4())

    asyncio.run(flow.arrived(link, SimpleNamespace(id=uuid.uuid4()), "c-1", "a@x.com"))

    assert done == ["saved", "published"]


def test_an_arrival_for_a_candidate_gone_since_does_nothing(monkeypatch):
    async def get(row_id):
        return None

    async def interviews(ids):
        raise AssertionError("not reached")

    monkeypatch.setattr(ats_candidates, "get", get)
    monkeypatch.setattr(flow.companies, "interviews", interviews)

    asyncio.run(handle("ats.candidate_arrived", {"ats_candidate_id": str(uuid.uuid4())}))
