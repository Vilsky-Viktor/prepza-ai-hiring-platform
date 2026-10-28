"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so a retry finds the action whole still to do."""

import uuid

import pytest

from ats.constants.ats import AtsProvider, CandidateStatus
from ats.core.db import Session
from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories import ats, ats_candidates, ats_results
from ats.services import accounts, reports
from ats.services import outbox as outbox_service
from tests.integration.transactions import transaction


async def broken(*args):
    raise RuntimeError("The database went away")


@pytest.fixture(autouse=True)
def unsent(monkeypatch):
    """The outbox isn't sent: what each action wrote stays to be read."""

    async def nothing():
        pass

    monkeypatch.setattr(outbox_service, "flush_quietly", nothing)


async def candidate(company, email: str = "ann@x.com", maker: str = "ann"):
    """A Workable connection made by `maker`, and a candidate it sent, invited."""
    await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", maker, "m-1")
    connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
    row = await transaction(ats_candidates.add, connection.id, None, uuid.uuid4(), "c-1", email)
    invite = uuid.uuid4()
    await transaction(ats_candidates.settle, row.id, CandidateStatus.INVITED, invite_id=invite)

    return connection, row, {"candidate_invite_id": str(invite), "grade": 80}


async def stored(model, row_id):
    async with Session() as session:
        return await session.get(model, row_id)


def test_deleting_an_account_keeps_its_candidates_when_forgetting_its_connections_fails(
    run, monkeypatch
):
    monkeypatch.setattr(ats, "forget_maker", broken)

    async def scenario():
        company, maker = uuid.uuid4(), f"maker-{uuid.uuid4()}"
        email = f"{uuid.uuid4()}@x.com"
        _, row, _ = await candidate(company, email, maker)

        with pytest.raises(RuntimeError):
            await accounts.remove_user(maker, email)

        left = await stored(AtsCandidate, row.id)
        await transaction(ats.delete_company, company)

        return left

    assert run(scenario()) is not None


def test_results_a_key_cant_write_stay_claimed_when_telling_the_company_fails(run, monkeypatch):
    monkeypatch.setattr(ats, "refuse_writes", broken)

    async def scenario():
        company = uuid.uuid4()
        connection, row, data = await candidate(company)
        await transaction(ats_results.claim, row.id, data)

        with pytest.raises(RuntimeError):
            await reports.write_refused(row, connection, data)

        left = await stored(AtsCandidate, row.id)
        await transaction(ats.delete_company, company)

        return left

    # Not kept (which frees the claim): the stale claim brings them back to the recovery job.
    assert run(scenario()).report_claimed_at is not None


def test_a_write_that_went_through_keeps_the_refusal_when_marking_it_reported_fails(
    run, monkeypatch
):
    async def scenario():
        company = uuid.uuid4()
        connection, row, _ = await candidate(company)
        await transaction(ats.refuse_writes, connection.id, {"recipient_id": str(company)})
        refused = await stored(AtsConnection, connection.id)
        monkeypatch.setattr(ats_results, "mark_reported", broken)

        with pytest.raises(RuntimeError):
            await reports.reported(row, refused)

        left = await stored(AtsConnection, connection.id)
        await transaction(ats.delete_company, company)

        return left

    assert run(scenario()).write_refused_at is not None
