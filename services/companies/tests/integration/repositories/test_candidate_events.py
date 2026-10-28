import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import (
    interview_generations,
    interviews,
    invite_expiry,
    invite_progress,
    invites,
)
from tests.integration import factories
from tests.integration.transactions import transaction


async def events_about(field: str, value: str) -> list[tuple[str, dict]]:
    async with Session() as session:
        rows = await session.scalars(select(OutboxEvent))

        return [(row.event_type, row.data) for row in rows if row.data.get(field) == value]


def test_a_candidates_start_bounce_expiry_and_removal_are_told_once_each(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        started, _ = await transaction(
            invites.upsert, interview.id, "s@example.com", "B", "A", "en"
        )
        bounced, _ = await transaction(
            invites.upsert, interview.id, "b@example.com", "B", "A", "en"
        )
        expiring, _ = await transaction(
            invites.upsert, interview.id, "e@example.com", "B", "A", "en"
        )
        # Twice each: a second start, bounce or expiry changes nothing and tells nobody again.
        await transaction(invite_progress.start, started.id, "u1")
        await transaction(invite_progress.start, started.id, "u1")
        await transaction(invite_progress.mark_undelivered, bounced.id, {"kind": "test"})
        await transaction(invite_progress.mark_undelivered, bounced.id, {"kind": "test"})
        later = datetime.now(UTC) + timedelta(seconds=1)
        await transaction(invite_expiry.mark_expired, expiring.id, later)
        await transaction(invite_expiry.mark_expired, expiring.id, later)
        await transaction(invites.remove, started, company.id)

        told = {}

        for invite in (started, bounced, expiring):
            told[invite.id] = [
                (event_type, data)
                for event_type, data in await events_about("candidate_invite_id", str(invite.id))
            ]

        return company, interview, started, bounced, expiring, told

    company, interview, started, bounced, expiring, told = run(scenario())

    def about(invite):
        return {
            "company_id": str(company.id),
            "interview_id": str(interview.id),
            "candidate_invite_id": str(invite.id),
        }

    assert told[started.id] == [
        ("candidate.started", about(started)),
        ("candidate.removed", {**about(started), "email": "s@example.com"}),
    ]
    assert told[bounced.id] == [("candidate.undelivered", about(bounced))]
    assert told[expiring.id] == [("candidate.expired", about(expiring))]


def test_an_interview_ready_says_whose_it_is(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        generation = uuid.uuid4()
        interview = await transaction(interviews.create, company.id, generation, "en", 60)
        await transaction(
            interview_generations.set_generated,
            generation,
            uuid.uuid4(),
            "Backend",
            None,
            {"kind": "x"},
            "ev1",
        )

        return company, interview, await events_about("interview_id", str(interview.id))

    company, interview, told = run(scenario())

    assert (
        "interview.ready",
        {"interview_id": str(interview.id), "company_id": str(company.id)},
    ) in told


def test_a_candidates_start_pledge_and_finish_times_are_kept_from_the_first_time(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(invites.upsert, interview.id, "t@example.com", "B", "A", "en")
        await transaction(invite_progress.start, invite.id, "u1")
        first = await transaction(invites.get, invite.id)
        # Back through the link later: the first start stays.
        await transaction(invite_progress.start, invite.id, "u1")
        await transaction(invite_progress.finish, invite.id, 80, False, None)
        await transaction(invite_progress.finish, invite.id, 80, False, None)

        return first.started_at, first.pledged_at, await transaction(invites.get, invite.id)

    started_at, pledged_at, done = run(scenario())

    assert started_at is not None and done.started_at == started_at
    # The pledge every first start carries, kept from that start too.
    assert pledged_at is not None and done.pledged_at == pledged_at
    assert done.finished_at is not None and done.finished_at >= started_at
