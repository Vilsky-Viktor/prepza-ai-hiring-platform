"""Every AI call the services record, stored in billing's database: once each, for whom it was,
the AI costs tab's sums, and what is forgotten and dropped."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from prepza_common.ai.ai_cap import spent_today
from prepza_common.ai.ai_constants import AI_USED, Category
from sqlalchemy import func, select

from billing.api.v1 import internal
from billing.constants.products import OwnerType
from billing.constants.usage import CHANGES_KEEP_DAYS, USAGE_KEEP_DAYS
from billing.core.db import Session
from billing.handlers import dispatch
from billing.integrations import names
from billing.models.limits import LimitChange
from billing.models.usage import AiUsage, LimitHit
from billing.repositories import usage
from billing.services import ai_costs, topups
from billing.services import usage as usage_service
from tests.integration.transactions import transaction

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


def call(**fields) -> dict:
    return {
        "action": "assistant_message",
        "service": "assistant",
        "model": "gpt-6.1-sol",
        "input_tokens": 1_000,
        "cached_input_tokens": 0,
        "output_tokens": 100,
        "audio_seconds": 0.0,
        "cost_usd": 0.5,
        "company_id": None,
        "user_id": None,
        "subject_id": None,
        "outcome": "ok",
        **fields,
    }


async def rows_of(column, value) -> list[AiUsage]:
    async with Session() as session:
        return list(await session.scalars(select(AiUsage).where(column == value)))


def test_a_redelivered_call_is_stored_and_counted_toward_the_cap_once(run, redis):
    acme, event_id = str(uuid.uuid4()), uuid.uuid4().hex

    async def scenario():
        before = await spent_today(redis())

        for _ in range(3):
            await dispatch.handle(AI_USED, call(company_id=acme), event_id, NOW)

        return await rows_of(AiUsage.company_id, acme), await spent_today(redis()) - before

    stored, added = run(scenario())

    assert [(row.event_id, row.category, float(row.cost)) for row in stored] == [
        (event_id, Category.UNPAID, 0.5)
    ]
    assert added == pytest.approx(0.5)


def test_a_company_is_paid_from_its_first_top_up_on(run, redis):
    acme, other = str(uuid.uuid4()), str(uuid.uuid4())

    async def scenario():
        txn = f"txn_{uuid.uuid4().hex}"
        await topups.grant(
            OwnerType.COMPANY, acme, 100, 1, txn, "topup_50", None, "3000", "USD", NOW
        )
        found = []

        for company_id, at in ((acme, NOW - timedelta(hours=1)), (acme, NOW), (other, NOW)):
            data = call(company_id=company_id)
            found.append(await usage_service.record_usage(uuid.uuid4().hex, at, data))

        before = await spent_today(redis())
        # A paid company's call is never counted toward the unpaid cap.
        await dispatch.handle(AI_USED, call(company_id=acme), uuid.uuid4().hex, NOW)

        return found, await spent_today(redis()) - before

    found, added = run(scenario())

    assert found == [Category.UNPAID, Category.PAID, Category.UNPAID]
    assert added == 0


def test_the_ai_costs_tab_sums_a_month(run, redis, monkeypatch):
    acme, beta, ann = str(uuid.uuid4()), str(uuid.uuid4()), f"ann-{uuid.uuid4().hex}"
    month = datetime(2001, 2, 3, tzinfo=UTC)
    generation = uuid.uuid4().hex

    async def company_names(ids):
        return {acme: "Acme"}

    async def user_emails(ids):
        return {ann: "ann@example.com"}

    monkeypatch.setattr(names, "company_names", company_names)
    monkeypatch.setattr(names, "user_emails", user_emails)
    calls = [
        # One interview generation of two calls, paid.
        (
            Category.PAID,
            call(
                action="interview_generation",
                company_id=acme,
                subject_id=generation,
                cost_usd=1.0,
                input_tokens=2_000,
                cached_input_tokens=500,
            ),
        ),
        (
            Category.PAID,
            call(
                action="interview_generation", company_id=acme, subject_id=generation, cost_usd=0.5
            ),
        ),
        # Two assistant messages, unpaid, and a minute of transcription.
        (Category.UNPAID, call(company_id=beta, user_id=ann, subject_id="m1", cost_usd=0.2)),
        (Category.UNPAID, call(company_id=beta, user_id=ann, subject_id="m2", cost_usd=0.1)),
        (
            Category.NO_COMPANY,
            call(
                action="transcription",
                model="gpt-transcribe",
                user_id=ann,
                audio_seconds=60.0,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0045,
            ),
        ),
        (Category.PREPZA, call(action="template_generation", cost_usd=0.2)),
    ]

    async def scenario():
        async with Session() as session:
            for day, (category, data) in enumerate(calls):
                at = month + timedelta(days=day % 2)
                kept = {"event_id": uuid.uuid4().hex, "occurred_at": at, "category": category}
                fields = {key: value for key, value in data.items() if key != "cost_usd"}
                cost = Decimal(str(data["cost_usd"]))
                session.add(AiUsage(**fields, **kept, cost=cost))

            await session.commit()

        return await ai_costs.ai_costs_out("2001-02")

    found = run(scenario())

    assert found.totals.spend == pytest.approx(2.0045)
    assert (found.totals.calls, found.totals.cached_input_tokens) == (6, 500)
    assert found.totals.input_tokens == 2_000 + 4 * 1_000
    shares = {part.category: (part.spend, part.calls) for part in found.categories}
    assert shares == {
        "paid": (pytest.approx(1.5), 2),
        "unpaid": (pytest.approx(0.3), 2),
        "no_company": (pytest.approx(0.0045), 1),
        "prepza": (pytest.approx(0.2), 1),
    }
    actions = {part.action: part for part in found.actions}
    # Two calls of one generation are one interview: its cost is both.
    interview = actions["interview_generation"]
    assert (interview.calls, interview.units, interview.unit_cost) == (2, 1, pytest.approx(1.5))
    assert (interview.paid_spend, interview.unpaid_spend) == (pytest.approx(1.5), 0)
    message = actions["assistant_message"]
    assert (message.units, message.unit_cost) == (2, pytest.approx(0.15))
    assert message.unpaid_spend == pytest.approx(0.3)
    # Transcription is priced by the minute.
    assert actions["transcription"].units == pytest.approx(1.0)
    assert actions["transcription"].unit_cost == pytest.approx(0.0045)
    models = {part.model: part for part in found.models}
    assert models["gpt-6.1-sol"].cached_share == pytest.approx(500 / 6_000)
    assert [(part.id, part.name, part.calls) for part in found.companies] == [
        (acme, "Acme", 2),
        (beta, None, 2),
    ]
    assert [(part.id, part.name) for part in found.users] == [(ann, "ann@example.com")]
    assert [(part.day.isoformat(), round(part.spend, 4)) for part in found.days] == [
        ("2001-02-03", 1.2045),
        ("2001-02-04", 0.8),
    ]
    assert found.by_month is False


def test_a_support_page_shows_the_last_30_days(run):
    acme = str(uuid.uuid4())
    now = datetime.now(UTC)

    async def scenario():
        for days, cost in ((1, 0.25), (29, 0.5), (31, 4.0)):
            data = call(company_id=acme, cost_usd=cost)
            await usage_service.record_usage(uuid.uuid4().hex, now - timedelta(days=days), data)

        return await ai_costs.spend_out(acme, None)

    found = run(scenario())

    assert (found.spend, found.calls, found.days) == (pytest.approx(0.75), 2, 30)


def test_a_deleted_user_or_company_is_forgotten_and_its_costs_stay(run):
    acme, ann = str(uuid.uuid4()), f"ann-{uuid.uuid4().hex}"

    async def scenario():
        event_id = uuid.uuid4().hex
        await usage_service.record_usage(event_id, NOW, call(company_id=acme, user_id=ann))
        hit = {"limit": "MAX_API_KEYS", "kind": "ours", "scope": "company"}
        await transaction(
            usage.store_hit, uuid.uuid4().hex, NOW, {**hit, "company_id": acme, "user_id": ann}
        )
        # Accounts' event, delivered twice: the second forgets nothing more.
        for _ in range(2):
            await dispatch.handle("user.deleted", {"user_id": ann, "email": ""}, "e-1", NOW)

        await internal.delete_company(acme, None)

        async with Session() as session:
            stored = await session.scalar(select(AiUsage).where(AiUsage.event_id == event_id))
            hits = await session.scalar(
                select(func.count(LimitHit.id)).where(
                    (LimitHit.user_id == ann) | (LimitHit.company_id == acme)
                )
            )

        return stored, hits

    stored, hits = run(scenario())

    assert (stored.company_id, stored.user_id, float(stored.cost)) == (None, None, 0.5)
    assert hits == 0


def test_usage_and_hits_go_after_13_months_and_limit_changes_after_24(run):
    now = datetime.now(UTC)
    kept_id, dropped_id = uuid.uuid4().hex, uuid.uuid4().hex
    marker = f"test-{uuid.uuid4().hex[:8]}"

    async def scenario():
        for event_id, days in ((kept_id, USAGE_KEEP_DAYS - 1), (dropped_id, USAGE_KEEP_DAYS + 1)):
            await usage_service.record_usage(event_id, now - timedelta(days=days), call())
            hit = {"limit": "MAX_API_KEYS", "kind": "ours", "scope": "company"}
            await transaction(usage.store_hit, event_id, now - timedelta(days=days), hit)

        async with Session() as session:
            for days in (CHANGES_KEEP_DAYS - 1, CHANGES_KEEP_DAYS + 1):
                session.add(
                    LimitChange(
                        name=marker,
                        old_value=None,
                        new_value=float(days),
                        changed_by="ann",
                        changed_by_email="ann@example.com",
                        changed_at=now - timedelta(days=days),
                    )
                )

            await session.commit()

        await usage.drop_old(Session, now, USAGE_KEEP_DAYS, CHANGES_KEEP_DAYS)

        async with Session() as session:
            calls = await session.scalars(
                select(AiUsage.event_id).where(AiUsage.event_id.in_([kept_id, dropped_id]))
            )
            hits = await session.scalars(
                select(LimitHit.event_id).where(LimitHit.event_id.in_([kept_id, dropped_id]))
            )
            changes = await session.scalars(
                select(LimitChange.new_value).where(LimitChange.name == marker)
            )

            return list(calls), list(hits), list(changes)

    calls, hits, changes = run(scenario())

    assert calls == [kept_id]
    assert hits == [kept_id]
    assert changes == [CHANGES_KEEP_DAYS - 1]
