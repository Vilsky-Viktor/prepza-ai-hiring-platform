import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from ats.constants.ats import STALE_CLAIM_MINUTES, AtsProvider, CandidateStatus
from ats.core.db import Session
from ats.models.ats import AtsCandidate
from ats.repositories import ats, ats_candidates, ats_results


def test_results_whose_write_was_cut_off_are_sent_again_and_only_after(run):
    """The server stopped while writing them back: they aren't marked as gone back, and once the
    claim is stale the recovery job finds them."""

    async def scenario():
        company = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await ats.connection(company, AtsProvider.WORKABLE)
        row = await ats_candidates.add(connection.id, None, uuid.uuid4(), "cut", "cut@x.com")
        invite = uuid.uuid4()
        await ats_candidates.settle(row.id, CandidateStatus.INVITED, invite_id=invite)
        data = {"candidate_invite_id": str(invite), "grade": 80}

        claimed = await ats_results.claim(row.id, data)
        # A second event while it's being written: nothing.
        again = await ats_results.claim(row.id, data)
        writing = [r.id for r in await ats_results.unreported()]

        # Cut off: the claim goes stale.
        async with Session() as session:
            stale = datetime.now(UTC) - timedelta(minutes=STALE_CLAIM_MINUTES + 1)
            await session.execute(
                update(AtsCandidate)
                .where(AtsCandidate.id == row.id)
                .values(report_claimed_at=stale)
            )
            await session.commit()

        [found] = [r for r in await ats_results.unreported() if r.id == row.id]
        retaken = await ats_results.claim(row.id, found.result)
        await ats_results.mark_reported(row.id)
        done = await ats_results.for_invite(invite)
        await ats.delete_company(company)

        return claimed, again, row.id in writing, found.result, retaken, done

    claimed, again, listed_while_writing, kept, retaken, done = run(scenario())

    assert (claimed, again, listed_while_writing) == (True, False, False)
    assert kept["grade"] == 80
    assert retaken is True
    assert done is None
