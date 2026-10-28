import asyncio
import uuid
from types import SimpleNamespace

import pytest

from companies.constants.invites import InviteStatus
from companies.repositories import candidates
from companies.services import candidate_results

FINISHED_ID = uuid.uuid4()
RUNNING_ID = uuid.uuid4()


@pytest.fixture
def saved(monkeypatch):
    """The results stored, by invite id."""
    rows = {}

    async def fake_save(results):
        rows.update(results)

    monkeypatch.setattr(candidates, "save_results", fake_save)

    return rows


def test_a_finished_candidate_missing_their_grade_gets_it_stored(saved):
    stale = SimpleNamespace(id=FINISHED_ID, status=InviteStatus.FINISHED, grade=None, flagged=False)
    current = SimpleNamespace(id=RUNNING_ID, status=InviteStatus.FINISHED, grade=80, flagged=False)
    totals = {
        str(FINISHED_ID): {"grade": 100, "finished": True},
        str(RUNNING_ID): {"grade": 80, "finished": True},
    }

    asyncio.run(candidate_results.sync([stale, current], totals))

    # Rounds didn't answer when the first finished; the second's grade is already stored.
    assert saved == {FINISHED_ID: (100, False)}
    assert stale.grade == 100
