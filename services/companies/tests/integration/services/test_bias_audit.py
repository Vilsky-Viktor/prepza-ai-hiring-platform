"""The owner's bias-audit export against a real database and Redis: only the company's
candidates who finished with a grade, narrowed to an interview or a span of days, recorded in
the action log, limited per company a day, and nothing about candidates' protected
characteristics stored anywhere."""

import csv
import io
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy import inspect, select, update
from testee_common.events.audit_actions import AuditAction, TargetKind
from testee_common.limits.limit_list import LIMITS_KEY

from companies.config import settings
from companies.constants.invites import InviteStatus
from companies.core.db import Session, engine
from companies.models.audit import AuditEvent
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import interviews, invites
from companies.services import bias_audit
from tests.integration import factories
from tests.integration.transactions import transaction

NOW = datetime(2026, 10, 20, 12, tzinfo=UTC)
# Words a column holding a protected characteristic, or a proxy for one, would be named by.
PROTECTED = {
    "sex",
    "gender",
    "race",
    "ethnicity",
    "religion",
    "disability",
    "birth",
    "age",
    "zip",
    "postcode",
    "nationality",
}


@pytest.fixture
def redis(monkeypatch):
    """The tests' real Redis, for the export's daily count."""
    client = Redis.from_url(settings.redis_url)
    monkeypatch.setattr(bias_audit, "get_redis", lambda: client)

    return client


async def candidate(interview, email: str, grade: int | None, finished_at=NOW):
    """A candidate of the interview: finished with `grade` at `finished_at`, or only invited
    when `grade` is None."""
    invite, _ = await transaction(invites.upsert, interview.id, email, "Backend", "Acme", "en")
    values = {"status": InviteStatus.INVITED}

    if grade is not None:
        values = {"status": InviteStatus.FINISHED, "grade": grade, "finished_at": finished_at}

    async with Session.begin() as session:
        await session.execute(
            update(CandidateInvite).where(CandidateInvite.id == invite.id).values(**values)
        )

    return invite


async def interview_of(company, title: str, pass_mark: int = 60):
    created = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
    await transaction(interviews.set_title, created.id, title)

    async with Session.begin() as session:
        await session.execute(
            update(Interview).where(Interview.id == created.id).values(pass_mark=pass_mark)
        )

    return await transaction(interviews.get, created.id)


async def company_with_candidates():
    """A company with two interviews and candidates in each, and another company's candidate."""
    owner = f"owner-{uuid.uuid4()}"
    company = await factories.company(f"Acme {uuid.uuid4()}", owner, "o@example.com")
    backend = await interview_of(company, "Backend", pass_mark=60)
    data = await interview_of(company, "=Data", pass_mark=50)
    await candidate(backend, "ann@example.com", 80)
    await candidate(backend, "bob@example.com", 50)
    await candidate(backend, "cyd@example.com", 70, NOW - timedelta(days=10))
    await candidate(backend, "dee@example.com", None)
    await candidate(data, "eve@example.com", 55)
    stranger = await factories.company(f"Other {uuid.uuid4()}", "stranger", "s@example.com")
    await candidate(await interview_of(stranger, "Theirs"), "zed@example.com", 90)

    return company, owner, backend, data


def parsed(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


async def logged(company_id) -> list[tuple]:
    async with Session() as session:
        rows = await session.scalars(select(AuditEvent).where(AuditEvent.company_id == company_id))

        return [(row.action, row.target_kind, row.target_id, row.target_label) for row in rows]


def test_the_export_lists_the_companys_finished_candidates_and_is_logged(run, redis):
    async def scenario():
        company, owner, backend, data = await company_with_candidates()
        text = await bias_audit.export(company, owner)

        return company, backend, data, parsed(text), await logged(company.id)

    company, backend, _data, rows, events = run(scenario())

    by_email = {row["candidate_email"]: row for row in rows}
    assert sorted(by_email) == [
        "ann@example.com",
        "bob@example.com",
        "cyd@example.com",
        "eve@example.com",
    ]
    # The median of the Backend interview's 80, 50 and 70 is 70: only a grade above it counts.
    assert [
        (by_email[e]["passed"], by_email[e]["above_median"])
        for e in ("ann@example.com", "bob@example.com", "cyd@example.com")
    ] == [
        ("true", "true"),
        ("false", "false"),
        ("true", "false"),
    ]
    assert by_email["ann@example.com"]["interview_id"] == str(backend.id)
    assert by_email["ann@example.com"]["grade"] == "80"
    assert by_email["ann@example.com"]["pass_mark"] == "60"
    assert by_email["ann@example.com"]["finished_on"] == "2026-10-20"
    # A title spreadsheets would read as a formula stays text.
    assert by_email["eve@example.com"]["interview_title"] == "'=Data"
    assert by_email["eve@example.com"]["pass_mark"] == "50"
    assert events == [
        (AuditAction.BIAS_AUDIT_EXPORTED, TargetKind.COMPANY, company.id, company.name)
    ]


def test_one_interview_and_a_span_of_days_narrow_it(run, redis):
    async def scenario():
        company, owner, backend, _ = await company_with_candidates()
        one = await bias_audit.export(company, owner, backend.id)
        span = await bias_audit.export(
            company, owner, None, NOW - timedelta(days=1), NOW + timedelta(days=1)
        )

        return backend, parsed(one), parsed(span), await logged(company.id)

    backend, one, span, events = run(scenario())

    assert sorted(row["candidate_email"] for row in one) == [
        "ann@example.com",
        "bob@example.com",
        "cyd@example.com",
    ]
    assert sorted(row["candidate_email"] for row in span) == [
        "ann@example.com",
        "bob@example.com",
        "eve@example.com",
    ]
    assert (AuditAction.BIAS_AUDIT_EXPORTED, TargetKind.INTERVIEW, backend.id, "Backend") in events


def test_another_companys_interview_is_not_found_and_not_counted(run, redis):
    async def scenario():
        company, owner, _, _ = await company_with_candidates()
        stranger = await factories.company(f"Else {uuid.uuid4()}", "else", "e@example.com")
        theirs = await interview_of(stranger, "Theirs")

        with pytest.raises(HTTPException) as refused:
            await bias_audit.export(company, owner, theirs.id)

        return (
            refused.value,
            await redis.exists(f"rate:bias-audit:{company.id}"),
            await logged(company.id),
        )

    refusal, counted, events = run(scenario())

    assert refusal.status_code == 404
    assert counted == 0
    assert events == []


def test_exports_are_limited_per_company_a_day(run, redis):
    async def scenario():
        await redis.hset(LIMITS_KEY, mapping={"BIAS_AUDIT_EXPORTS_PER_DAY": 2})

        try:
            company, owner, _, _ = await company_with_candidates()
            other, other_owner, _, _ = await company_with_candidates()
            await bias_audit.export(company, owner)
            await bias_audit.export(company, owner)

            with pytest.raises(HTTPException) as refused:
                await bias_audit.export(company, owner)

            # Another company's exports count apart.
            await bias_audit.export(other, other_owner)
        finally:
            await redis.hdel(LIMITS_KEY, "BIAS_AUDIT_EXPORTS_PER_DAY")
            await redis.aclose()

        return refused.value

    refusal = run(scenario())

    assert refusal.status_code == 429
    assert 0 < int(refusal.headers["Retry-After"]) <= 24 * 60 * 60


def test_no_table_holds_a_protected_characteristic(run):
    """The export brings no demographic data in: the company joins its own categories outside
    testee, so no column anywhere could keep one."""

    async def scenario():
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync: [
                    (table, column["name"])
                    for table in inspect(sync).get_table_names()
                    for column in inspect(sync).get_columns(table)
                ]
            )

    columns = run(scenario())

    assert columns
    assert [
        (table, name) for table, name in columns if PROTECTED & set(name.lower().split("_"))
    ] == []
