import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.audit_actions import AuditAction
from prepza_common.constants import DELETED_USER, VIA_ASSISTANT
from sqlalchemy import func, select, update

from app.constants.audit import AUDIT_RETENTION_DAYS
from app.models.audit import AuditEvent
from app.storage import accounts, audit, companies
from app.storage.db import Session


def test_audit_events_list_newest_first_age_out_and_go_with_the_company(run):
    target = uuid.uuid4()

    async def scenario():
        company = await companies.create(f"Audit {uuid.uuid4()}", "ann", "ann@example.com")
        await audit.record(company.id, "ann", AuditAction.PASS_MARK_CHANGED, target)
        await audit.record(company.id, "ann", AuditAction.RESULTS_VIEWED, target)
        await audit.record(company.id, "ann", AuditAction.TOPICS_APPROVED)
        listed = await audit.list_for_company(company.id, 0, 10)
        # The first event is three years old: retention takes it, and only it.
        async with Session() as session:
            await session.execute(
                update(AuditEvent)
                .where(AuditEvent.id == listed[-1].id)
                .values(created_at=datetime.now(UTC) - timedelta(days=3 * 365))
            )
            await session.commit()

        aged = await audit.delete_before(datetime.now(UTC) - timedelta(days=AUDIT_RETENTION_DAYS))
        kept = await audit.list_for_company(company.id, 0, 10)
        await companies.delete(company.id)

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
        company = await companies.create(name, "owner", "owner@example.com")
        await audit.record(company.id, user, AuditAction.RESULTS_VIEWED)
        await audit.record(company.id, "owner", AuditAction.TOPICS_APPROVED)
        exported = (await accounts.export(user, "gone@example.com"))["company_decisions"]
        await audit.forget_user(user)
        # Safe to repeat.
        await audit.forget_user(user)
        listed = await audit.list_for_company(company.id, 0, 10)
        left = (await accounts.export(user, "gone@example.com"))["company_decisions"]
        await companies.delete(company.id)

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
        company = await companies.create(f"Audit {uuid.uuid4()}", user, f"{user}@example.com")
        await audit.record(company.id, user, AuditAction.RESULTS_VIEWED, target)
        await audit.record(company.id, user, AuditAction.RESULTS_VIEWED, target, via=VIA_ASSISTANT)
        listed = await audit.list_for_company(company.id, 0, 10)
        exported = (await accounts.export(user, f"{user}@example.com"))["company_decisions"]
        await companies.delete(company.id)

        return listed, exported

    listed, exported = run(scenario())

    assert sorted(row.via or "" for row in listed) == ["", VIA_ASSISTANT]
    assert sorted(row["via"] or "" for row in exported) == ["", VIA_ASSISTANT]


def test_old_audit_events_are_deleted_in_batches_and_new_ones_kept(run):
    from prepza_common.db import delete_in_batches

    async def scenario():
        company = await companies.create(f"Batches {uuid.uuid4()}", "ann", "ann@example.com")

        for _ in range(5):
            await audit.record(company.id, "ann", AuditAction.PASS_MARK_CHANGED)

        await audit.record(company.id, "ann", AuditAction.TOPICS_APPROVED)
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
        kept = await audit.list_for_company(company.id, 0, 10)
        await companies.delete(company.id)

        return deleted, kept

    deleted, kept = run(scenario())

    assert deleted == 5
    assert [row.action for row in kept] == [AuditAction.TOPICS_APPROVED]
