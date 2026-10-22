import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.constants.ats import AtsProvider, CandidateStatus, FailReason
from app.models.ats import AtsCandidate
from app.storage import ats, ats_candidates, not_invited
from app.storage.db import Session

SINCE = datetime(2026, 10, 1, tzinfo=UTC)
UNTIL = datetime(2026, 10, 18, tzinfo=UTC)


async def failed_at(row_id):
    async with Session() as session:
        return await session.scalar(select(AtsCandidate.failed_at).where(AtsCandidate.id == row_id))


async def set_failed_at(row_id, at):
    async with Session() as session:
        await session.execute(
            update(AtsCandidate).where(AtsCandidate.id == row_id).values(failed_at=at)
        )
        await session.commit()


async def connected(company):
    await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")

    return await ats.connection(company, AtsProvider.WORKABLE)


def test_a_failed_invite_keeps_the_time_it_first_failed(run):
    async def scenario():
        company = uuid.uuid4()
        connection = await connected(company)
        row = await ats_candidates.add(connection.id, None, uuid.uuid4(), "c-1", "a@example.com")
        before = await failed_at(row.id)
        await ats_candidates.settle(row.id, CandidateStatus.FAILED, FailReason.LIMIT)
        first = await failed_at(row.id)
        await ats_candidates.settle(row.id, CandidateStatus.FAILED, FailReason.CREDITS)
        second = await failed_at(row.id)
        await ats.delete_company(company)

        return before, first, second

    before, first, second = run(scenario())

    assert before is None
    assert first is not None
    assert second == first


def test_between_lists_the_companies_candidates_first_failed_in_the_window_newest_first(run):
    async def scenario():
        company, other = uuid.uuid4(), uuid.uuid4()
        connection = await connected(company)
        theirs = await connected(other)
        interview = uuid.uuid4()
        failures = {
            "older": (connection.id, SINCE + timedelta(days=1)),
            "newer": (connection.id, UNTIL - timedelta(days=1)),
            "at until": (connection.id, UNTIL),
            "at since": (connection.id, SINCE),
            "after": (connection.id, UNTIL + timedelta(seconds=1)),
            "theirs": (theirs.id, SINCE + timedelta(days=2)),
        }

        for candidate_id, (connection_id, at) in failures.items():
            row = await ats_candidates.add(
                connection_id, None, interview, candidate_id, f"{uuid.uuid4()}@example.com"
            )
            await ats_candidates.settle(row.id, CandidateStatus.FAILED, FailReason.LIMIT)
            await set_failed_at(row.id, at)

        # Failed in the window, then invited on a retry: no longer listed.
        invited = await ats_candidates.add(
            connection.id, None, interview, "invited", "inv@example.com"
        )
        await ats_candidates.settle(invited.id, CandidateStatus.FAILED, FailReason.LIMIT)
        await set_failed_at(invited.id, SINCE + timedelta(days=3))
        await ats_candidates.settle(invited.id, CandidateStatus.INVITED, invite_id=uuid.uuid4())
        rows = await not_invited.between([company], SINCE, UNTIL, 2)
        total = await not_invited.count_between([company], SINCE, UNTIL)
        await ats.delete_company(company)
        await ats.delete_company(other)

        listed = [(row.candidate_id, row.failed_at, conn.company_id) for row, conn in rows]

        return listed, total, company

    found, total, company = run(scenario())

    assert found == [
        ("at until", UNTIL, company),
        ("newer", UNTIL - timedelta(days=1), company),
    ]
    # Only the newest are listed; every one is counted.
    assert total == 3
