"""Candidates from an ATS: one row each, claimed once, counted, found for a top-up and reported."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from ats.constants.ats import AtsProvider, CandidateStatus, FailReason
from ats.constants.events import ATS_CANDIDATE_ARRIVED
from ats.core.db import Session
from ats.models.ats import AtsCandidate
from ats.models.outbox import OutboxEvent
from ats.repositories import ats, ats_candidates, ats_links, ats_results
from tests.integration.transactions import transaction

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


def test_a_candidate_is_one_row_claimed_once_counted_and_reported_once(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann", "m-1"
        )
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        first = await transaction(
            ats_candidates.add, connection.id, link_id, interview, "c-1", "A@x.com"
        )
        again = await transaction(
            ats_candidates.add, connection.id, link_id, interview, "c-1", "a@x.com"
        )
        claims = [
            await transaction(ats_candidates.claim, first.id, (CandidateStatus.WAITING,)),
            await transaction(ats_candidates.claim, first.id, (CandidateStatus.WAITING,)),
        ]
        invite = uuid.uuid4()
        await transaction(
            ats_candidates.settle, first.id, CandidateStatus.INVITED, invite_id=invite
        )
        other = await transaction(
            ats_candidates.add, connection.id, link_id, interview, "c-2", "b@x.com"
        )
        await transaction(ats_candidates.settle, other.id, CandidateStatus.FAILED, "credits")
        counts = await transaction(ats_candidates.counts, company)
        await ats_candidates.requeue_not_invited(Session, company, link_id)
        failed = await transaction(ats_candidates.not_invited, company, link_id)
        to_report = await transaction(ats_results.for_invite, invite)
        await transaction(ats_results.mark_reported, first.id)
        reported = await transaction(ats_results.for_invite, invite)
        await transaction(ats.delete_company, company)

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
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        row = await transaction(
            ats_candidates.add, connection.id, None, interview, "c-1", "a@x.com"
        )
        first = await transaction(ats_candidates.claim, row.id, (CandidateStatus.WAITING,))
        # Started just now: not stale, so nobody else may claim it.
        fresh = await transaction(ats_candidates.claim, row.id, (CandidateStatus.WAITING,))
        stale_before = [i for i in await transaction(ats_candidates.recoverable) if i.id == row.id]

        async with Session() as session:
            await session.execute(
                update(AtsCandidate)
                .where(AtsCandidate.id == row.id)
                .values(claimed_at=datetime.now(UTC) - timedelta(minutes=11))
            )
            await session.commit()

        stale_after = [i for i in await transaction(ats_candidates.recoverable) if i.id == row.id]
        again = await transaction(ats_candidates.claim, row.id, (CandidateStatus.WAITING,))
        await transaction(ats.delete_company, company)

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
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        await transaction(ats.connect, company, AtsProvider.GREENHOUSE, "…1234", "sealed", "ann")
        await transaction(
            ats.connect, other_company, AtsProvider.WORKABLE, "other", "sealed", "bob"
        )
        workable = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        greenhouse = await transaction(ats.connection, company, AtsProvider.GREENHOUSE)
        theirs = await transaction(ats.connection, other_company, AtsProvider.WORKABLE)
        links = {
            connection.id: await transaction(
                ats_links.add_link,
                connection.company_id,
                connection.id,
                interview,
                JOB,
                STAGE,
                "ann",
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
            row = await transaction(
                ats_candidates.add,
                connection_id,
                link_id,
                interview,
                candidate_id,
                f"{candidate_id}@x.com",
            )

            if status != CandidateStatus.WAITING:
                await transaction(ats_candidates.settle, row.id, status, reason)

        async with Session() as session:
            await session.execute(
                update(AtsCandidate)
                .where(
                    AtsCandidate.connection_id == workable.id, AtsCandidate.candidate_id == "old"
                )
                .values(created_at=datetime.now(UTC) - timedelta(days=31))
            )
            await session.commit()

        found = await transaction(ats_candidates.requeue_short, company)

        await ats_candidates.requeue_short_rest(Session, company)
        await transaction(ats.delete_company, company)
        await transaction(ats.delete_company, other_company)

        return found

    found = run(scenario())

    # Not the candidates of an unlinked job, nor those sent more than 30 days ago.
    assert sorted(row.candidate_id for row in found) == ["credits", "credits-other-ats"]


def test_results_are_claimed_once_until_kept(run):
    async def scenario():
        company = uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann", "m-1"
        )
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        row = await transaction(
            ats_candidates.add, connection.id, None, uuid.uuid4(), "c-1", "a@x.com"
        )
        claims = [
            await transaction(ats_results.claim, row.id, {"name": "sent"}),
            await transaction(ats_results.claim, row.id, {"name": "sent"}),
        ]
        await transaction(ats_results.keep, row.id, {"name": "kept"})
        kept = [
            item.result for item in await transaction(ats_results.unreported) if item.id == row.id
        ]
        claims.append(await transaction(ats_results.claim, row.id, {"name": "sent"}))
        await transaction(ats.delete_company, company)

        return claims, kept

    claims, kept = run(scenario())

    # Two events at once: one writes. Results kept free the claim, for the recovery job.
    assert claims == [True, False, True]
    assert kept == [{"name": "kept"}]


def test_an_interviews_waiting_candidates_come_one_batch_at_a_time(run, monkeypatch):
    monkeypatch.setattr(ats_candidates, "INVITE_BATCH", 2)

    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann", "m-1"
        )
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )

        for number in range(3):
            await transaction(
                ats_candidates.add,
                connection.id,
                link_id,
                interview,
                f"c-{number}",
                f"c{number}@x.com",
            )

        return [row.candidate_id for row in await transaction(ats_candidates.waiting, interview)]

    # The oldest first; the third is left for the recovery job.
    assert run(scenario()) == ["c-0", "c-1"]


def test_a_new_candidate_is_saved_with_one_arrival_event_and_a_repeat_adds_none(run):
    async def scenario():
        company, interview = uuid.uuid4(), uuid.uuid4()
        await transaction(
            ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann", "m-1"
        )
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        row = await transaction(
            ats_candidates.add, connection.id, link_id, interview, "c-9", "z@x.com"
        )
        # The web hook comes again: the same row, and no second event.
        await transaction(ats_candidates.add, connection.id, link_id, interview, "c-9", "z@x.com")

        async with Session() as session:
            events = await session.scalars(
                select(OutboxEvent.data).where(OutboxEvent.event_type == ATS_CANDIDATE_ARRIVED)
            )
            mine = [data for data in events if data["ats_candidate_id"] == str(row.id)]

        await transaction(ats.delete_company, company)

        return mine

    assert len(run(scenario())) == 1
