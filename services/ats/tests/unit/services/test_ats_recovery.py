import asyncio
import uuid
from types import SimpleNamespace

import httpx
import pytest

from ats.constants.ats import MAX_INVITE_ATTEMPTS
from ats.integrations import companies
from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories import ats, ats_candidates, ats_results
from ats.services import ats_candidates as flow
from tests.unit.conftest import interview


@pytest.fixture
def world(monkeypatch, companies_api):
    """A working connection, an interview ready at companies, candidate rows in memory (their
    outcomes recorded), and invites recorded by the faked companies service."""
    connection = AtsConnection(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        provider="workable",
        status="connected",
        created_by="ann",
    )
    interview_id = uuid.uuid4()
    companies_api["interviews"][interview_id] = interview(
        connection.company_id, interview_id=interview_id
    )
    state = {
        "connection": connection,
        "interview_id": interview_id,
        "api": companies_api,
        "settled": {},
        "postponed": [],
        "notices": [],
    }

    async def connection_by_id(connection_id):
        return connection

    async def claim(row_id, statuses):
        return True

    async def settle(row_id, status_, reason=None, invite_id=None, notice=None):
        state["settled"][row_id] = (status_, reason)

        if notice:
            state["notices"].append(notice)

    async def postpone(row_id):
        state["postponed"].append(row_id)

    async def nothing():
        return None

    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)

    async def connections_by_ids(connection_ids):
        found = {item: await connection_by_id(item) for item in connection_ids}

        return {item: connection for item, connection in found.items() if connection}

    monkeypatch.setattr(ats, "connections_by_ids", connections_by_ids)
    monkeypatch.setattr(ats_candidates, "claim", claim)
    monkeypatch.setattr(ats_candidates, "settle", settle)
    monkeypatch.setattr(ats_candidates, "postpone", postpone)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", nothing)

    return state


def candidate(state, email="ann@example.com", attempts=0, interview_id=None) -> AtsCandidate:
    return AtsCandidate(
        id=uuid.uuid4(),
        connection_id=state["connection"].id,
        interview_id=interview_id or state["interview_id"],
        candidate_id=email,
        email=email,
        status="waiting",
        attempts=attempts,
    )


def failing_companies(monkeypatch):
    async def invite(interview_id, email, sender_id, name=None):
        raise httpx.ConnectTimeout("companies didn't answer")

    monkeypatch.setattr(companies, "invite", invite)


def test_companies_not_answering_leaves_the_candidate_waiting_without_a_notice(world, monkeypatch):
    failing_companies(monkeypatch)
    row = candidate(world)
    asyncio.run(flow.invite_all([row]))

    assert world["postponed"] == [row.id]
    assert world["settled"] == {} and world["notices"] == []


def test_the_last_attempt_keeps_the_candidate_as_not_invited_with_a_notice(world, monkeypatch):
    failing_companies(monkeypatch)
    row = candidate(world, attempts=MAX_INVITE_ATTEMPTS - 1)
    asyncio.run(flow.invite_all([row]))

    assert world["postponed"] == []
    assert world["settled"] == {row.id: ("failed", "other")}
    assert len(world["notices"]) == 1


def test_a_candidate_whose_interview_cant_be_read_waits_for_the_recovery_job(world, monkeypatch):
    async def interviews(ids):
        raise httpx.ConnectTimeout("companies didn't answer")

    async def add(connection_id, link_id, interview_id, candidate_id, email, name=None):
        return candidate(world, email)

    monkeypatch.setattr(companies, "interviews", interviews)
    monkeypatch.setattr(ats_candidates, "add", add)
    link = type("Link", (), {"id": uuid.uuid4(), "interview_id": world["interview_id"]})
    # Answered, not raised: the row is saved, and the recovery job invites it.
    asyncio.run(flow.arrived(link, world["connection"], "c-1", "ann@example.com"))

    assert world["api"]["sent"] == [] and world["settled"] == {}


def test_one_run_invites_a_batch_and_leaves_the_rest_waiting(world, monkeypatch):
    monkeypatch.setattr(flow, "INVITE_BATCH", 2)
    not_ready = uuid.uuid4()
    world["api"]["interviews"][not_ready] = interview(
        world["connection"].company_id, ready=False, interview_id=not_ready
    )
    # An interview still being made doesn't take a place in the batch.
    rows = [candidate(world, "early@example.com", interview_id=not_ready)] + [
        candidate(world, f"{name}@example.com") for name in ("ann", "bob", "cid")
    ]
    asyncio.run(flow.invite_all(rows))

    assert [email for email, _ in world["api"]["sent"]] == ["ann@example.com", "bob@example.com"]


def test_a_broken_connections_candidates_wait(world):
    world["connection"].status = "broken"
    asyncio.run(flow.invite_all([candidate(world)]))

    assert world["api"]["sent"] == [] and world["settled"] == {}


def test_the_recovery_job_invites_waiting_candidates_and_sends_kept_results(world, monkeypatch):
    waiting = candidate(world)
    kept = [
        AtsCandidate(id=uuid.uuid4(), result={"candidate_invite_id": "one"}),
        AtsCandidate(id=uuid.uuid4(), result={"candidate_invite_id": "two"}),
    ]
    reported = []

    async def recoverable():
        return [waiting]

    async def unreported():
        return kept

    async def report(data):
        # One ATS failing doesn't stop the others' results.
        if data["candidate_invite_id"] == "one":
            raise httpx.ConnectTimeout("the ATS didn't answer")

        reported.append(data["candidate_invite_id"])

    monkeypatch.setattr(ats_candidates, "recoverable", recoverable)
    monkeypatch.setattr(ats_results, "unreported", unreported)
    monkeypatch.setattr(flow, "report", report)

    assert asyncio.run(flow.recover()) == 1
    assert world["api"]["sent"] == [("ann@example.com", "ann")]
    assert world["settled"][waiting.id][0] == "invited"
    assert reported == ["two"]


def test_the_recovery_job_starts_no_new_result_late_in_the_run(world, monkeypatch):
    kept = [AtsCandidate(id=uuid.uuid4(), result={"candidate_invite_id": n}) for n in "abc"]
    reported = []
    # Each look at the clock is 20 seconds later: a slow ATS.
    clock = iter(range(0, 1000, 20))

    async def nothing():
        return []

    async def unreported():
        return kept

    async def report(data):
        reported.append(data["candidate_invite_id"])

    monkeypatch.setattr(ats_candidates, "recoverable", nothing)
    monkeypatch.setattr(ats_results, "unreported", unreported)
    monkeypatch.setattr(flow, "report", report)
    monkeypatch.setattr(flow, "time", SimpleNamespace(monotonic=lambda: next(clock)))
    asyncio.run(flow.recover())

    # Started at 0, so 20 seconds in it sends one; at 40, past REPORT_SECONDS, it stops.
    assert reported == ["a"]


def test_the_recovery_job_stops_inviting_when_its_time_is_up(world, monkeypatch):
    clock = SimpleNamespace(now=100.0)

    async def invite(row, connection, interview):
        world["settled"][row.id] = ("invited", None)
        # Each invite takes 8 seconds.
        clock.now += 8

    monkeypatch.setattr(flow.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(flow, "invite", invite)
    rows = [candidate(world, f"c{index}@example.com") for index in range(5)]

    asyncio.run(flow.invite_all(rows, stop_at=120.0))

    # Started at 100, 108 and 116; not at 124.
    assert len(world["settled"]) == 3
