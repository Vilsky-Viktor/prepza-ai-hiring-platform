"""Candidates from an ATS: one row each, claimed once, counted, found for a top-up and reported."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from app.constants.ats import AtsProvider, CandidateStatus, FailReason
from app.models.ats import AtsCandidate
from app.storage import ats, ats_candidates, ats_links, ats_results
from app.storage.db import Session

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


def test_a_candidate_is_one_row_claimed_once_counted_and_reported_once(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann", "m-1")
        connection = await ats.connection(company, AtsProvider.WORKABLE)
        link_id = await ats_links.add_link(
            connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        first = await ats_candidates.add(connection.id, link_id, interview, "c-1", "A@x.com")
        again = await ats_candidates.add(connection.id, link_id, interview, "c-1", "a@x.com")
        claims = [
            await ats_candidates.claim(first.id, (CandidateStatus.WAITING,)),
            await ats_candidates.claim(first.id, (CandidateStatus.WAITING,)),
        ]
        invite = uuid.uuid4()
        await ats_candidates.settle(first.id, CandidateStatus.INVITED, invite_id=invite)
        other = await ats_candidates.add(connection.id, link_id, interview, "c-2", "b@x.com")
        await ats_candidates.settle(other.id, CandidateStatus.FAILED, "credits")
        counts = await ats_candidates.counts(company)
        failed = await ats_candidates.not_invited(company, link_id)
        to_report = await ats_results.for_invite(invite)
        await ats_results.mark_reported(first.id)
        reported = await ats_results.for_invite(invite)
        await ats.delete_company(company)

        return first, again, claims, counts[link_id], failed, to_report, reported

    first, again, claims, counts, failed, to_report, reported = run(scenario())

    assert again.id == first.id and first.email == "a@x.com"
    assert claims == [True, False]
    assert counts == {"invited": 1, "failed": 1}
    assert [row.candidate_id for row in failed] == ["c-2"]
    assert to_report[0].id == first.id and to_report[1].member_id == "m-1"
    assert reported is None


def test_an_invite_cut_off_midway_can_be_claimed_again_after_a_while(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await ats.connection(company, AtsProvider.WORKABLE)
        row = await ats_candidates.add(connection.id, None, interview, "c-1", "a@x.com")
        first = await ats_candidates.claim(row.id, (CandidateStatus.WAITING,))
        # Started just now: not stale, so nobody else may claim it.
        fresh = await ats_candidates.claim(row.id, (CandidateStatus.WAITING,))
        stale_before = [i for i in await ats_candidates.recoverable() if i.id == row.id]

        async with Session() as session:
            await session.execute(
                update(AtsCandidate)
                .where(AtsCandidate.id == row.id)
                .values(claimed_at=datetime.now(UTC) - timedelta(minutes=11))
            )
            await session.commit()

        stale_after = [i for i in await ats_candidates.recoverable() if i.id == row.id]
        again = await ats_candidates.claim(row.id, (CandidateStatus.WAITING,))
        await ats.delete_company(company)

        return first, fresh, stale_before, stale_after, again

    first, fresh, stale_before, stale_after, again = run(scenario())

    assert (first, fresh) == (True, False)
    assert stale_before == [] and len(stale_after) == 1
    assert again is True


def test_a_top_up_finds_only_the_companys_recent_linked_candidates_short_of_credits(run):
    async def scenario():
        company = uuid.uuid4()
        other_company = uuid.uuid4()
        interview = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        await ats.connect(company, AtsProvider.GREENHOUSE, "…1234", "sealed", "ann")
        await ats.connect(other_company, AtsProvider.WORKABLE, "other", "sealed", "bob")
        workable = await ats.connection(company, AtsProvider.WORKABLE)
        greenhouse = await ats.connection(company, AtsProvider.GREENHOUSE)
        theirs = await ats.connection(other_company, AtsProvider.WORKABLE)
        links = {
            connection.id: await ats_links.add_link(
                connection.company_id, connection.id, interview, JOB, STAGE, "ann"
            )
            for connection in (workable, greenhouse, theirs)
        }
        rows = {
            "credits": (workable.id, CandidateStatus.FAILED, FailReason.CREDITS),
            "credits-other-ats": (greenhouse.id, CandidateStatus.FAILED, FailReason.CREDITS),
            "limit": (workable.id, CandidateStatus.FAILED, FailReason.LIMIT),
            "paused": (workable.id, CandidateStatus.FAILED, FailReason.PAUSED),
            "invited": (workable.id, CandidateStatus.INVITED, None),
            "waiting": (workable.id, CandidateStatus.WAITING, None),
            "other-company": (theirs.id, CandidateStatus.FAILED, FailReason.CREDITS),
            "unlinked": (workable.id, CandidateStatus.FAILED, FailReason.CREDITS),
            "old": (workable.id, CandidateStatus.FAILED, FailReason.CREDITS),
        }

        for candidate_id, (connection_id, status, reason) in rows.items():
            link_id = None if candidate_id == "unlinked" else links[connection_id]
            row = await ats_candidates.add(
                connection_id, link_id, interview, candidate_id, f"{candidate_id}@x.com"
            )

            if status != CandidateStatus.WAITING:
                await ats_candidates.settle(row.id, status, reason)

        async with Session() as session:
            await session.execute(
                update(AtsCandidate)
                .where(
                    AtsCandidate.connection_id == workable.id, AtsCandidate.candidate_id == "old"
                )
                .values(created_at=datetime.now(UTC) - timedelta(days=31))
            )
            await session.commit()

        found = await ats_candidates.short_of_credits(company)
        await ats.delete_company(company)
        await ats.delete_company(other_company)

        return found

    found = run(scenario())

    # Not the candidates of an unlinked job, nor those sent more than 30 days ago.
    assert sorted(row.candidate_id for row in found) == ["credits", "credits-other-ats"]


def test_results_are_claimed_once_until_kept(run):
    async def scenario():
        company = uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann", "m-1")
        connection = await ats.connection(company, AtsProvider.WORKABLE)
        row = await ats_candidates.add(connection.id, None, uuid.uuid4(), "c-1", "a@x.com")
        claims = [
            await ats_results.claim(row.id, {"name": "sent"}),
            await ats_results.claim(row.id, {"name": "sent"}),
        ]
        await ats_results.keep(row.id, {"name": "kept"})
        kept = [item.result for item in await ats_results.unreported() if item.id == row.id]
        claims.append(await ats_results.claim(row.id, {"name": "sent"}))
        await ats.delete_company(company)

        return claims, kept

    claims, kept = run(scenario())

    # Two events at once: one writes. Results kept free the claim, for the recovery job.
    assert claims == [True, False, True]
    assert kept == [{"name": "kept"}]
