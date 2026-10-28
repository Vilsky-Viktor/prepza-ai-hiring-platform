"""A deleted company's and a deleted interview's invites go a batch at a time, each batch its
own transaction with its guests announced; the company's action log and interviews too. More
rows than a batch all go, the events are saved once, and another company keeps its rows."""

import uuid

import pytest
from prepza_common.db import db
from prepza_common.events.audit_actions import AuditAction
from sqlalchemy import func, select, update

from companies.constants.invites import InviteStatus
from companies.core.db import Session
from companies.models.audit import AuditEvent
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.models.outbox import OutboxEvent
from companies.repositories import audit, batch_deletion, companies, interviews, invites


@pytest.fixture(autouse=True)
def small_batches(monkeypatch):
    monkeypatch.setattr(batch_deletion, "DELETE_BATCH", 2)
    monkeypatch.setattr(db, "DELETE_BATCH", 2)


async def count(model, *conditions) -> int:
    async with Session() as session:
        return await session.scalar(select(func.count()).select_from(model).where(*conditions))


async def events(event_type: str, key: str, value: str) -> list[dict]:
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent.data).where(OutboxEvent.event_type == event_type)
        )

        return [data for data in rows if data.get(key) == value]


async def company_with_candidates():
    """A company with three interviews, five invites on the first (two guests, one finished),
    and three actions logged."""
    company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
    made = [await interviews.create(company.id, uuid.uuid4(), "en", 60) for _ in range(3)]
    sent = []

    for number in range(5):
        invite, _ = await invites.upsert(
            made[0].id,
            f"c{number}-{uuid.uuid4()}@example.com",
            "Backend",
            "Acme",
            "en",
            sign_in=number > 1,
        )
        sent.append(invite)

    async with Session() as session:
        await session.execute(
            update(CandidateInvite)
            .where(CandidateInvite.id == sent[4].id)
            .values(status=InviteStatus.FINISHED)
        )
        await session.commit()

    for _ in range(3):
        await audit.record(company.id, "owner", AuditAction.PASS_MARK_CHANGED)

    return company, made, sent


def test_a_deleted_companys_rows_go_batch_after_batch(run):
    async def scenario():
        company, _, sent = await company_with_candidates()
        other, _, _ = await company_with_candidates()
        await companies.delete(company.id)
        left = [
            await count(CandidateInvite, CandidateInvite.company_id == company.id),
            await count(AuditEvent, AuditEvent.company_id == company.id),
            await count(Interview, Interview.company_id == company.id),
        ]
        others = [
            await count(CandidateInvite, CandidateInvite.company_id == other.id),
            await count(AuditEvent, AuditEvent.company_id == other.id),
            await count(Interview, Interview.company_id == other.id),
        ]
        announced = await events("company.deleted", "company_id", str(company.id))
        gone = await companies.get(company.id)
        await companies.delete(other.id)

        return sent, left, others, announced, gone, await guests_announced()

    sent, left, others, announced, gone, guests = run(scenario())

    assert gone is None
    assert left == [0, 0, 0]
    assert others == [5, 3, 3]
    assert len(announced) == 1
    assert {f"guest-{sent[0].id}", f"guest-{sent[1].id}"} <= guests


def test_a_removed_interviews_invites_go_batch_after_batch(run):
    async def scenario():
        company, made, sent = await company_with_candidates()
        removed = await interviews.remove(made[0].id)
        left = await count(CandidateInvite, CandidateInvite.interview_id == made[0].id)
        announced = await events("interview.deleted", "interview_id", str(made[0].id))
        await companies.delete(company.id)

        return sent, removed, left, announced, await guests_announced()

    sent, removed, left, announced, guests = run(scenario())

    # The four not finished come back, to give their credits back; the finished one goes too.
    assert sorted(row[1] for row in removed) == sorted(invite.email for invite in sent[:4])
    assert left == 0
    assert len(announced) == 1
    assert {f"guest-{sent[0].id}", f"guest-{sent[1].id}"} <= guests


async def guests_announced() -> set[str]:
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent.data).where(OutboxEvent.event_type == "guests.deleted")
        )

        return {user_id for data in rows for user_id in data["user_ids"]}
