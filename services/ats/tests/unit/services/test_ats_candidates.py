import asyncio
import base64
import hashlib
import hmac
import json
import uuid

import pytest
from fastapi import HTTPException, status

from ats.helpers.ats import workable_signed
from ats.models.ats import AtsCandidate, AtsConnection, AtsJobLink
from ats.repositories import ats, ats_candidates, ats_links
from ats.services import ats as integrations
from ats.services import ats_candidates as flow
from ats.services import ats_webhooks as hooks
from tests.unit.arrivals import deliver_arrivals
from tests.unit.conftest import interview

TOKEN = "account-token"
LINK_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def sign(body: bytes, encoding="hex") -> str:
    digest = hmac.new(TOKEN.encode(), body, hashlib.sha256).digest()

    return digest.hex() if encoding == "hex" else base64.b64encode(digest).decode()


def event(email="ann@example.com", job="A1", kind="candidate_moved") -> bytes:
    return json.dumps(
        {"event_type": kind, "data": {"id": "c-1", "email": email, "job": {"shortcode": job}}}
    ).encode()


def test_only_bodies_signed_with_the_token_count_in_hex_or_base64():
    body = event()

    assert workable_signed(TOKEN, body, sign(body))
    assert workable_signed(TOKEN, body, sign(body, "base64"))
    assert not workable_signed("another-token", body, sign(body))
    assert not workable_signed(TOKEN, body + b" ", sign(body))


@pytest.fixture
def world(monkeypatch, companies_api):
    """A linked job, its connection and interview (in companies), the candidate rows in memory,
    and invites recorded by the faked companies service."""
    connection = AtsConnection(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        provider="workable",
        status="connected",
        created_by="ann",
    )
    link = AtsJobLink(
        id=LINK_ID, connection_id=connection.id, interview_id=INTERVIEW_ID, job_id="A1"
    )
    companies_api["interviews"][INTERVIEW_ID] = interview(
        connection.company_id, interview_id=INTERVIEW_ID
    )
    state = {"rows": {}, "claims": True, "notices": [], "flushed": 0, "api": companies_api}

    async def get_link(session, link_id):
        return (link, connection) if link_id == LINK_ID else None

    async def key(found):
        return {"subdomain": "acme", "token": TOKEN}

    async def add(session, connection_id, link_id, interview_id, candidate_id, email, name=None):
        return state["rows"].setdefault(
            candidate_id,
            AtsCandidate(
                id=uuid.uuid4(),
                connection_id=connection_id,
                interview_id=interview_id,
                candidate_id=candidate_id,
                email=email,
                name=name,
                status="waiting",
                attempts=0,
            ),
        )

    async def claim(session, row_id, statuses):
        return state["claims"]

    async def settle(session, row_id, status_, reason=None, invite_id=None, notice=None):
        if notice:
            state["notices"].append(notice)

        for row in state["rows"].values():
            if row.id == row_id:
                row.status, row.reason = status_, reason

    async def flush():
        state["flushed"] += 1

    monkeypatch.setattr(ats_links, "link", get_link)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(ats_candidates, "add", add)
    monkeypatch.setattr(ats_candidates, "claim", claim)
    monkeypatch.setattr(ats_candidates, "settle", settle)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", flush)
    deliver_arrivals(monkeypatch, state["rows"], then=flush, connection=connection)

    return state, companies_api["interviews"][INTERVIEW_ID]


def receive(body, signature=None):
    asyncio.run(
        hooks.receive_workable(LINK_ID, body, sign(body) if signature is None else signature)
    )


def test_a_moved_candidate_is_invited_as_whoever_connected_workable(world):
    state, _ = world
    receive(event())

    assert state["api"]["sent"] == [("ann@example.com", "ann")]
    assert state["rows"]["c-1"].status == "invited"


def test_an_unsigned_event_is_refused_and_invites_nobody(world):
    state, _ = world

    with pytest.raises(HTTPException) as refused:
        receive(event(), signature="forged")

    assert refused.value.status_code == 401
    assert state["api"]["sent"] == []


def test_another_event_job_or_a_candidate_without_email_is_ignored(world):
    state, _ = world
    receive(event(kind="candidate_created"))
    receive(event(job="B2"))
    receive(event(email=""))

    assert state["api"]["sent"] == [] and state["rows"] == {}


def test_a_second_event_that_doesnt_win_the_claim_invites_nobody(world):
    state, _ = world
    state["claims"] = False
    receive(event())

    assert state["api"]["sent"] == []


def test_a_candidate_waits_while_the_interview_is_being_made(world):
    state, found = world
    found["ready"] = False
    receive(event())

    assert state["api"]["sent"] == []
    assert state["rows"]["c-1"].status == "waiting"


@pytest.mark.parametrize(
    ("refusal", "reason"),
    [
        (status.HTTP_402_PAYMENT_REQUIRED, "credits"),
        (status.HTTP_429_TOO_MANY_REQUESTS, "limit"),
        (status.HTTP_503_SERVICE_UNAVAILABLE, "paused"),
    ],
)
def test_a_refused_invite_is_kept_with_its_reason_to_retry(world, refusal, reason):
    state, _ = world
    state["api"]["refuse"] = refusal
    receive(event())

    assert (state["rows"]["c-1"].status, state["rows"]["c-1"].reason) == ("failed", reason)
    # Owners and admins hear why, with a link to the ATS's own page, which retries.
    [notice] = state["notices"]
    assert notice["kind"] == "ats_not_invited"
    # It names the ATS the candidate came from.
    assert notice["data"] == {
        "ats": "Workable",
        "email": "ann@example.com",
        "title": "Accountant",
        "reason": reason,
    }
    assert notice["link"].endswith("/integrations/workable")
    # Once by the web hook (its arrival), once by the arrival's handler (the notice).
    assert state["flushed"] == 2


def test_a_connection_whose_maker_is_no_longer_an_editor_asks_for_reconnecting(world, monkeypatch):
    state, _ = world
    broken = []

    async def mark_broken(session, connection_id, notice):
        broken.append(connection_id)

    monkeypatch.setattr(ats, "mark_broken", mark_broken)
    state["api"]["refuse"] = status.HTTP_403_FORBIDDEN
    receive(event())

    assert len(broken) == 1
    assert state["rows"]["c-1"].status == "failed"
    assert state["api"]["sent"] == []


@pytest.mark.parametrize("answer", [status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT])
def test_an_interview_gone_or_not_ready_at_companies_keeps_the_candidate_waiting(world, answer):
    state, _ = world
    state["api"]["refuse"] = answer
    receive(event())

    assert state["rows"]["c-1"].status == "waiting"
    assert state["notices"] == []


def test_an_interview_companies_doesnt_have_invites_nobody(world):
    state, _ = world
    state["api"]["interviews"].clear()
    receive(event())

    assert state["api"]["sent"] == []
    assert state["rows"]["c-1"].status == "waiting"


def test_waiting_candidates_are_invited_once_the_interview_is_ready(world, monkeypatch):
    state, found = world
    found["ready"] = False
    receive(event())
    found["ready"] = True

    async def waiting(session, interview_id):
        return [row for row in state["rows"].values() if row.interview_id == interview_id]

    async def connection_by_id(session, connection_id):
        return AtsConnection(id=connection_id, created_by="ann", status="connected")

    monkeypatch.setattr(ats_candidates, "waiting", waiting)
    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)

    async def connections_by_ids(session, connection_ids):
        found = {item: await connection_by_id(session, item) for item in connection_ids}

        return {item: connection for item, connection in found.items() if connection}

    monkeypatch.setattr(ats, "connections_by_ids", connections_by_ids)
    asyncio.run(flow.invite_waiting(INTERVIEW_ID))

    assert state["api"]["sent"] == [("ann@example.com", "ann")]
    assert state["rows"]["c-1"].status == "invited"


def test_a_top_up_invites_the_candidates_kept_for_lack_of_credits(world, monkeypatch):
    state, _ = world
    state["api"]["refuse"] = status.HTTP_402_PAYMENT_REQUIRED
    receive(event())
    state["api"]["refuse"] = None
    asked = []

    async def requeue_short(session, company_id):
        asked.append(company_id)

        return [row for row in state["rows"].values() if row.reason == "credits"]

    async def requeue_short_rest(sessions, company_id):
        asked.append(company_id)

    async def connection_by_id(session, connection_id):
        return AtsConnection(id=connection_id, created_by="ann", status="connected")

    monkeypatch.setattr(ats_candidates, "requeue_short", requeue_short)
    monkeypatch.setattr(ats_candidates, "requeue_short_rest", requeue_short_rest)
    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)

    async def connections_by_ids(session, connection_ids):
        found = {item: await connection_by_id(session, item) for item in connection_ids}

        return {item: connection for item, connection in found.items() if connection}

    monkeypatch.setattr(ats, "connections_by_ids", connections_by_ids)
    company_id = uuid.uuid4()
    asyncio.run(flow.topped_up(company_id))

    assert asked == [company_id, company_id]
    assert state["api"]["sent"] == [("ann@example.com", "ann")]
    assert state["rows"]["c-1"].status == "invited"


def test_the_name_the_ats_sent_goes_with_the_invite(world, companies_api):
    d = json.loads(event())
    d["data"]["name"] = " Ann Lee "
    receive(json.dumps(d).encode())

    assert companies_api["names"] == {"ann@example.com": "Ann Lee"}
