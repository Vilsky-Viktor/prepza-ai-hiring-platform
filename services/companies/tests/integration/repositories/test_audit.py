import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from testee_common.config.constants import DELETED_USER, VIA_ASSISTANT
from testee_common.events.audit_actions import AuditAction

from companies.constants.audit import AUDIT_RETENTION_DAYS
from companies.core.db import Session
from companies.models.audit import AuditEvent
from companies.repositories import accounts, audit
from tests.integration import factories
from tests.integration.transactions import transaction


def test_audit_events_list_newest_first_age_out_and_go_with_the_company(run):
    target = uuid.uuid4()

    async def scenario():
        company = await factories.company(f"Audit {uuid.uuid4()}", "ann", "ann@example.com")
        await transaction(audit.record, company.id, "ann", AuditAction.PASS_MARK_CHANGED, target)
        await transaction(audit.record, company.id, "ann", AuditAction.RESULTS_VIEWED, target)
        await transaction(audit.record, company.id, "ann", AuditAction.TOPICS_APPROVED)
        listed = await transaction(audit.list_for_company, company.id, 0, 10)
        # The first event is three years old: retention takes it, and only it.
        async with Session() as session:
            await session.execute(
                update(AuditEvent)
                .where(AuditEvent.id == listed[-1].id)
                .values(created_at=datetime.now(UTC) - timedelta(days=3 * 365))
            )
            await session.commit()

        aged = await audit.delete_before(
            Session, datetime.now(UTC) - timedelta(days=AUDIT_RETENTION_DAYS)
        )
        kept = await transaction(audit.list_for_company, company.id, 0, 10)
        await factories.deleted(company.id)

        async with Session() as session:
            left = await session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.company_id == company.id)
            )

        return listed, aged, kept, left

    listed, aged, kept, left = run(scenario())

    assert [row.action for row in listed] == [
        AuditAction.TOPICS_APPROVED,
        AuditAction.RESULTS_VIEWED,
        AuditAction.PASS_MARK_CHANGED,
    ]
    assert listed[0].target_id is None and listed[1].target_id == target
    assert aged >= 1
    assert [row.action for row in kept] == [
        AuditAction.TOPICS_APPROVED,
        AuditAction.RESULTS_VIEWED,
    ]
    assert left == 0


def test_a_deleted_users_decisions_are_exported_then_stay_without_their_id(run):
    user = f"gone-{uuid.uuid4()}"

    async def scenario():
        name = f"Audit {uuid.uuid4()}"
        company = await factories.company(name, "owner", "owner@example.com")
        await transaction(audit.record, company.id, user, AuditAction.RESULTS_VIEWED)
        await transaction(audit.record, company.id, "owner", AuditAction.TOPICS_APPROVED)
        exported = (await transaction(accounts.export, user, "gone@example.com"))[
            "company_decisions"
        ]
        await audit.forget_user(Session, user)
        # Safe to repeat.
        await audit.forget_user(Session, user)
        listed = await transaction(audit.list_for_company, company.id, 0, 10)
        left = (await transaction(accounts.export, user, "gone@example.com"))["company_decisions"]
        await factories.deleted(company.id)

        return name, exported, listed, left

    name, exported, listed, left = run(scenario())

    assert [(row["company"], row["action"]) for row in exported] == [
        (name, AuditAction.RESULTS_VIEWED)
    ]
    assert sorted(row.user_id for row in listed) == sorted([DELETED_USER, "owner"])
    assert left == []


def test_a_read_through_the_assistant_is_listed_and_exported_with_via(run):
    user = f"reader-{uuid.uuid4()}"
    target = uuid.uuid4()

    async def scenario():
        company = await factories.company(f"Audit {uuid.uuid4()}", user, f"{user}@example.com")
        await transaction(audit.record, company.id, user, AuditAction.RESULTS_VIEWED, target)
        await transaction(
            audit.record, company.id, user, AuditAction.RESULTS_VIEWED, target, via=VIA_ASSISTANT
        )
        listed = await transaction(audit.list_for_company, company.id, 0, 10)
        exported = (await transaction(accounts.export, user, f"{user}@example.com"))[
            "company_decisions"
        ]
        await factories.deleted(company.id)

        return listed, exported

    listed, exported = run(scenario())

    assert sorted(row.via or "" for row in listed) == ["", VIA_ASSISTANT]
    assert sorted(row["via"] or "" for row in exported) == ["", VIA_ASSISTANT]


def test_old_audit_events_are_deleted_in_batches_and_new_ones_kept(run):
    from testee_common.db.db import delete_in_batches

    async def scenario():
        company = await factories.company(f"Batches {uuid.uuid4()}", "ann", "ann@example.com")

        for _ in range(5):
            await transaction(audit.record, company.id, "ann", AuditAction.PASS_MARK_CHANGED)

        await transaction(audit.record, company.id, "ann", AuditAction.TOPICS_APPROVED)
        old = AuditEvent.company_id == company.id, AuditEvent.action != AuditAction.TOPICS_APPROVED

        async with Session() as session:
            await session.execute(
                update(AuditEvent).where(*old).values(created_at=datetime(2000, 1, 1, tzinfo=UTC))
            )
            await session.commit()

        cutoff = datetime(2001, 1, 1, tzinfo=UTC)
        mine = AuditEvent.company_id == company.id
        # Two at a time: three batches, the last one short.
        deleted = await delete_in_batches(
            Session, AuditEvent, mine, AuditEvent.created_at < cutoff, batch=2
        )
        kept = await transaction(audit.list_for_company, company.id, 0, 10)
        await factories.deleted(company.id)

        return deleted, kept

    deleted, kept = run(scenario())

    assert deleted == 5
    assert [row.action for row in kept] == [AuditAction.TOPICS_APPROVED]


def test_a_deleted_users_actions_lose_their_id_batch_after_batch(run, monkeypatch):
    from testee_common.db import db

    monkeypatch.setattr(db, "DELETE_BATCH", 2)
    user = f"gone-{uuid.uuid4()}"

    async def scenario():
        company = await factories.company(f"Audit {uuid.uuid4()}", "owner", "owner@example.com")

        for _ in range(5):
            await transaction(audit.record, company.id, user, AuditAction.PASS_MARK_CHANGED)

        await transaction(audit.record, company.id, "owner", AuditAction.TOPICS_APPROVED)
        await audit.forget_user(Session, user)
        listed = await transaction(audit.list_for_company, company.id, 0, 10)
        await factories.deleted(company.id)

        return listed

    listed = run(scenario())

    # More than a batch, all without the id; the other member's stays theirs.
    assert sorted(row.user_id for row in listed) == [DELETED_USER] * 5 + ["owner"]


def test_two_deleted_members_who_viewed_one_candidate_the_same_day_are_both_forgotten(run):
    """Both views fall to the deleted user on the same day: one view stays, and neither
    deletion fails on the one-view-a-day rule."""
    first, second = f"gone-{uuid.uuid4()}", f"gone-{uuid.uuid4()}"
    candidate = uuid.uuid4()

    async def scenario():
        company = await factories.company(f"Views {uuid.uuid4()}", "owner", "o@example.com")
        await transaction(audit.record_view, company.id, first, candidate)
        await transaction(audit.record_view, company.id, second, candidate)
        await audit.forget_user(Session, first)
        await audit.forget_user(Session, second)
        listed = await transaction(audit.list_for_company, company.id, 0, 10)
        await factories.deleted(company.id)

        return listed

    listed = run(scenario())

    assert [(row.user_id, row.action) for row in listed] == [
        (DELETED_USER, AuditAction.RESULTS_VIEWED)
    ]
