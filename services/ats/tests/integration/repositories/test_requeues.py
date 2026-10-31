"""Candidates not invited put back to waiting: invited again from a linked job's page, or after
a top-up for those short of credits."""

import uuid

from ats.constants.ats import AtsProvider, CandidateStatus, FailReason
from ats.core.db import Session
from ats.repositories import ats, ats_candidates, ats_links
from tests.integration.transactions import transaction

JOB = {"id": "A1", "name": "Accountant"}
STAGE = {"id": "assessment", "name": "Assessment"}


def test_invite_again_and_a_top_up_put_not_invited_candidates_back_to_waiting(run):
    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        rows = {}

        for name, reason in (("limit", FailReason.LIMIT), ("credits", FailReason.CREDITS)):
            rows[name] = await transaction(
                ats_candidates.add, connection.id, link_id, interview, name, "a@x"
            )
            await transaction(ats_candidates.postpone, rows[name].id)
            await transaction(ats_candidates.settle, rows[name].id, CandidateStatus.FAILED, reason)

        topped_up = await transaction(ats_candidates.requeue_short, company)

        await ats_candidates.requeue_short_rest(Session, company)
        await transaction(
            ats_candidates.settle, rows["credits"].id, CandidateStatus.FAILED, "credits"
        )
        await ats_candidates.requeue_not_invited(Session, company, link_id)
        retried = await transaction(ats_candidates.not_invited, company, link_id)
        await transaction(ats.delete_company, company)

        return topped_up, retried

    topped_up, retried = run(scenario())

    # Each put back to waiting, with its attempts reset; a top-up only those short of credits.
    assert [(row.candidate_id, row.status, row.reason, row.attempts) for row in topped_up] == [
        ("credits", "waiting", None, 0)
    ]
    assert sorted((row.candidate_id, row.status, row.attempts) for row in retried) == [
        ("credits", "waiting", 0),
        ("limit", "waiting", 0),
    ]


def test_more_not_invited_candidates_than_a_batch_all_wait_again(run, monkeypatch):
    from sqlalchemy import select
    from testee_common.db import db

    from ats.core.db import Session
    from ats.models.ats import AtsCandidate

    monkeypatch.setattr(db, "DELETE_BATCH", 2)
    monkeypatch.setattr(ats_candidates, "INVITE_BATCH", 2)

    async def statuses(connection_id) -> list[str]:
        async with Session() as session:
            query = select(AtsCandidate.status).where(AtsCandidate.connection_id == connection_id)

            return list(await session.scalars(query))

    async def scenario():
        company = uuid.uuid4()
        interview = uuid.uuid4()
        await transaction(ats.connect, company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await transaction(ats.connection, company, AtsProvider.WORKABLE)
        link_id = await transaction(
            ats_links.add_link, connection.company_id, connection.id, interview, JOB, STAGE, "ann"
        )
        rows = [
            await transaction(
                ats_candidates.add, connection.id, link_id, interview, f"c-{n}", f"{n}@x.com"
            )
            for n in range(5)
        ]

        async def fail_all():
            for row in rows:
                await transaction(
                    ats_candidates.settle, row.id, CandidateStatus.FAILED, FailReason.CREDITS
                )

        await fail_all()
        topped_up = await transaction(ats_candidates.requeue_short, company)
        await ats_candidates.requeue_short_rest(Session, company)
        after_top_up = await statuses(connection.id)
        await fail_all()
        await ats_candidates.requeue_not_invited(Session, company, link_id)
        retried = await transaction(ats_candidates.not_invited, company, link_id)
        after_retry = await statuses(connection.id)
        await transaction(ats.delete_company, company)

        return rows, topped_up, after_top_up, retried, after_retry

    rows, topped_up, after_top_up, retried, after_retry = run(scenario())

    # The oldest batch is invited now; every one waits again, the rest for the recovery job.
    assert [row.id for row in topped_up] == [row.id for row in rows[:2]]
    assert after_top_up == ["waiting"] * 5
    assert len(retried) == 2
    assert after_retry == ["waiting"] * 5
