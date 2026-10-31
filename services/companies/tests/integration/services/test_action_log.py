"""A company's action log against the real database: its filters, the events other services
send, results views kept to one row a day, retention, and the rows read back with who and what.
Each test makes its own company and deletes it."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text, update
from testee_common.events.audit_actions import AuditAction, AuditGroup, TargetKind

from companies.core.db import Session
from companies.models.audit import AuditEvent
from companies.repositories import audit, interviews, invites
from companies.services import action_log, audit_events, retention
from tests.integration import factories
from tests.integration.transactions import transaction

NOW = datetime.now(UTC)


async def new_company(owner: str):
    return await factories.company(f"Log {uuid.uuid4()}", owner, f"{owner}@example.com")


async def rows_of(company_id) -> list[AuditEvent]:
    query = (
        select(AuditEvent)
        .where(AuditEvent.company_id == company_id)
        .order_by(AuditEvent.created_at)
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def move(event_id, created_at, day=None) -> None:
    values = {"created_at": created_at} | ({"day": day} if day else {})

    async with Session() as session:
        await session.execute(update(AuditEvent).where(AuditEvent.id == event_id).values(**values))
        await session.commit()


def event(company_id, action, at, user_id="ann", **extra) -> dict:
    return {
        "company_id": str(company_id),
        "user_id": user_id,
        "action": action,
        "target_kind": extra.get("target_kind"),
        "target_id": extra.get("target_id"),
        "target_label": extra.get("target_label"),
        "removed": extra.get("removed"),
    }


def test_the_filters_find_one_members_one_groups_or_some_days_actions_newest_first(run):
    async def scenario():
        acme = await new_company("ann")
        await transaction(audit.record, acme.id, "ann", AuditAction.INTERVIEW_CREATED)
        await transaction(audit.record, acme.id, "bob", AuditAction.CANDIDATE_INVITED)
        await transaction(audit.record, acme.id, "ann", AuditAction.MEMBER_INVITED)
        old = (await transaction(audit.list_for_company, acme.id, 0, 10))[-1]
        await move(old.id, NOW - timedelta(days=40))

        def actions(rows):
            return [row.action for row in rows]

        found = [
            actions(await transaction(audit.list_for_company, acme.id, 0, 10)),
            actions(await transaction(audit.list_for_company, acme.id, 0, 10, user_id="ann")),
            actions(
                await transaction(
                    audit.list_for_company, acme.id, 0, 10, group=AuditGroup.CANDIDATES
                )
            ),
            actions(
                await transaction(
                    audit.list_for_company,
                    acme.id,
                    0,
                    10,
                    start=NOW - timedelta(days=50),
                    end=NOW - timedelta(days=30),
                )
            ),
            actions(await transaction(audit.list_for_company, acme.id, 1, 1)),
        ]
        await factories.deleted(acme.id)

        return found

    every, ann, candidates, earlier, second = run(scenario())

    assert every == [
        AuditAction.MEMBER_INVITED,
        AuditAction.CANDIDATE_INVITED,
        AuditAction.INTERVIEW_CREATED,
    ]
    assert ann == [AuditAction.MEMBER_INVITED, AuditAction.INTERVIEW_CREATED]
    assert candidates == [AuditAction.CANDIDATE_INVITED]
    assert earlier == [AuditAction.INTERVIEW_CREATED]
    assert second == [AuditAction.CANDIDATE_INVITED]


def test_the_filters_have_their_indexes(run):
    async def scenario():
        query = text("SELECT indexdef FROM pg_indexes WHERE tablename = 'audit_events'")

        async with Session() as session:
            return [row[0] for row in await session.execute(query)]

    indexes = " ".join(run(scenario()))

    assert "(company_id, user_id, created_at)" in indexes
    assert '(company_id, "group", created_at)' in indexes


def test_another_services_event_is_stored_once_at_its_own_time_and_never_for_a_gone_company(run):
    async def scenario():
        acme = await new_company("ann")
        gone = await new_company("gil")
        await factories.deleted(gone.id)
        earlier = NOW - timedelta(hours=2)
        paid = event(acme.id, AuditAction.TOP_UP_PAID, NOW, target_kind=TargetKind.COMPANY)
        late = event(acme.id, AuditAction.ATS_CONNECTED, earlier, target_label="Workable")

        await audit_events.record("billing-1", paid, NOW)
        # Redelivered: stored once.
        await audit_events.record("billing-1", paid, NOW)
        # Sent before the top-up but arriving after it: placed by when it happened.
        await audit_events.record("ats-1", late, earlier)
        await audit_events.record("ats-2", event(gone.id, AuditAction.ATS_CONNECTED, NOW), NOW)
        listed = await transaction(audit.list_for_company, acme.id, 0, 10)
        await factories.deleted(acme.id)

        async with Session() as session:
            kept_for_gone = await session.scalar(
                select(AuditEvent.id).where(AuditEvent.event_id == "ats-2")
            )

        return listed, kept_for_gone

    listed, kept_for_gone = run(scenario())

    assert [(row.action, row.group, row.target_label) for row in listed] == [
        (AuditAction.TOP_UP_PAID, AuditGroup.BILLING, None),
        (AuditAction.ATS_CONNECTED, AuditGroup.INTEGRATIONS, "Workable"),
    ]
    assert listed[1].created_at < listed[0].created_at
    assert kept_for_gone is None


def test_results_viewed_are_one_row_a_member_candidate_and_day(run):
    candidate = uuid.uuid4()

    async def scenario():
        acme = await new_company("ann")
        # Views at the same moment: one row.
        await asyncio.gather(
            *(transaction(audit.record_view, acme.id, "ann", candidate) for _ in range(5))
        )
        once = await rows_of(acme.id)
        # The same view yesterday: today's is another row.
        yesterday = NOW - timedelta(days=1)
        await move(once[0].id, yesterday, yesterday.date())
        await transaction(audit.record_view, acme.id, "ann", candidate, via="assistant")
        # Another member's view of the same candidate today: a row of its own.
        await transaction(audit.record_view, acme.id, "bob", candidate)
        # Ann again today: her row moves to now.
        await transaction(audit.record_view, acme.id, "ann", candidate)
        rows = await rows_of(acme.id)
        await factories.deleted(acme.id)

        return once, rows

    once, rows = run(scenario())

    assert len(once) == 1
    assert sorted((row.user_id, row.day) for row in rows) == sorted(
        [
            ("ann", (NOW - timedelta(days=1)).date()),
            ("ann", NOW.date()),
            ("bob", NOW.date()),
        ]
    )
    todays_ann = next(row for row in rows if row.user_id == "ann" and row.day == NOW.date())
    # The latest view's way: in the app.
    assert todays_ann.via is None
    assert all(row.target_kind == TargetKind.CANDIDATE for row in rows)


def test_retention_takes_actions_older_than_12_months_only(run):
    async def scenario():
        acme = await new_company("ann")
        await transaction(audit.record, acme.id, "ann", AuditAction.COMPANY_RENAMED)
        await transaction(audit.record, acme.id, "ann", AuditAction.LOGO_CHANGED)
        old, recent = await rows_of(acme.id)
        await move(old.id, NOW - timedelta(days=370))
        await move(recent.id, NOW - timedelta(days=330))
        await retention.delete_old_audit_events()
        left = [row.action for row in await rows_of(acme.id)]
        await factories.deleted(acme.id)

        return left

    assert run(scenario()) == [AuditAction.LOGO_CHANGED]


def test_rows_name_members_and_candidates_only_while_they_are_there(run):
    async def scenario():
        acme = await new_company("ann")
        interview = await transaction(interviews.create, acme.id, uuid.uuid4(), "en", 60)
        invite, _ = await transaction(
            invites.upsert, interview.id, "cara@example.com", "Backend", acme.name, "en"
        )
        await transaction(
            audit.record,
            acme.id,
            "ann",
            AuditAction.EXTRA_TIME_SET,
            invite.id,
            target_kind=TargetKind.CANDIDATE,
        )
        await transaction(
            audit.record,
            acme.id,
            "left",
            AuditAction.CANDIDATE_DELETED,
            uuid.uuid4(),
            target_kind=TargetKind.CANDIDATE,
        )
        await audit_events.record(
            f"api-{uuid.uuid4()}",
            event(
                acme.id,
                AuditAction.API_KEY_PERMISSIONS_CHANGED,
                NOW,
                target_kind=TargetKind.API_KEY,
                target_id=str(uuid.uuid4()),
                target_label="Zapier",
                removed=["mcp"],
            ),
            # After the two rows just recorded: NOW is when the module loaded, which earlier
            # tests can leave more than a second behind.
            datetime.now(UTC) + timedelta(seconds=1),
        )
        rows = await action_log.page(acme.id, 0, 10)
        await factories.deleted(acme.id)

        return rows

    rows = run(scenario())

    assert [(row.action, row.user_email, row.target, row.removed) for row in rows] == [
        (AuditAction.API_KEY_PERMISSIONS_CHANGED, "ann@example.com", "Zapier", ["mcp"]),
        (AuditAction.CANDIDATE_DELETED, None, None, None),
        (AuditAction.EXTRA_TIME_SET, "ann@example.com", "cara@example.com", None),
    ]
