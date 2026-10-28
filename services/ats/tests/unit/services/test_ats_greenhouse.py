import asyncio
import hashlib
import hmac
import json
import uuid

import pytest
from fastapi import HTTPException

from ats.models.ats import AtsCandidate, AtsConnection, AtsJobLink
from ats.repositories import ats, ats_candidates, ats_links
from ats.services import ats as integrations
from ats.services import ats_candidates as flow
from ats.services import ats_webhooks as hooks
from tests.unit.arrivals import deliver_arrivals
from tests.unit.conftest import interview

SECRET = "webhook-secret"
CONNECTION_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def sign(body: bytes) -> str:
    return "sha256 " + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def event(email="ann@example.com", job=101, stage=None, action="candidate_stage_change") -> bytes:
    stage = stage or {"id": 7, "name": "Assessment"}
    application = {
        "id": 55,
        "candidate": {"id": 44, "email_addresses": [{"value": email}]},
        "current_stage": stage,
        "jobs": [{"id": job}],
    }

    return json.dumps({"action": action, "payload": {"application": application}}).encode()


@pytest.fixture
def world(monkeypatch, companies_api):
    """A Greenhouse connection with job 101 linked at stage `state["stage"]`, the candidate rows
    in memory, and invites recorded instead of sent."""
    connection = AtsConnection(
        id=CONNECTION_ID,
        company_id=uuid.uuid4(),
        provider="greenhouse",
        status="connected",
        created_by="ann",
    )
    companies_api["interviews"][INTERVIEW_ID] = interview(
        connection.company_id, interview_id=INTERVIEW_ID
    )
    state = {"connection": connection, "stage": "7", "rows": {}, "sent": companies_api["sent"]}

    async def connection_by_id(connection_id):
        return state["connection"] if connection_id == CONNECTION_ID else None

    async def link_for_job(connection_id, job_id):
        if job_id != "101":
            return None

        return AtsJobLink(
            id=uuid.uuid4(),
            connection_id=connection_id,
            interview_id=INTERVIEW_ID,
            job_id=job_id,
            stage_id=state["stage"],
        )

    async def key(found):
        return {"client_id": "id", "client_secret": "secret", "webhook_secret": SECRET}

    async def add(connection_id, link_id, interview_id, candidate_id, email, name=None):
        return state["rows"].setdefault(
            candidate_id,
            AtsCandidate(
                id=uuid.uuid4(),
                connection_id=connection_id,
                interview_id=interview_id,
                candidate_id=candidate_id,
                email=email,
                name=name,
            ),
        )

    async def claim(row_id, statuses):
        return True

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)
    monkeypatch.setattr(ats_links, "link_for_job", link_for_job)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(ats_candidates, "add", add)
    monkeypatch.setattr(ats_candidates, "claim", claim)
    monkeypatch.setattr(ats_candidates, "settle", nothing)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", nothing)
    deliver_arrivals(monkeypatch, state["rows"])

    return state


def receive(body, signature=None, connection_id=CONNECTION_ID):
    signature = sign(body) if signature is None else signature
    asyncio.run(hooks.receive_greenhouse(connection_id, body, signature))


def test_a_candidate_moved_into_the_linked_stage_is_invited(world):
    receive(event())

    assert world["sent"] == [("ann@example.com", "ann")]
    # Kept as "<candidate>:<application>", for the note on the application later.
    assert list(world["rows"]) == ["44:55"]


def test_the_linked_stage_matches_by_name_too(world):
    world["stage"] = "Assessment"
    receive(event(stage={"id": 999, "name": "Assessment"}))

    assert world["sent"] == [("ann@example.com", "ann")]


def test_an_unsigned_event_is_refused_and_invites_nobody(world):
    with pytest.raises(HTTPException) as refused:
        receive(event(), signature="sha256 forged")

    assert refused.value.status_code == 401
    assert world["sent"] == []


def test_a_ping_another_stage_or_job_or_a_candidate_without_email_is_ignored(world):
    receive(b'{"action": "ping"}')
    receive(event(action="new_candidate_application"))
    receive(event(stage={"id": 8, "name": "Offer"}))
    receive(event(job=202))
    receive(event(email=None))

    assert world["sent"] == [] and world["rows"] == {}


def test_an_unknown_or_non_greenhouse_connection_is_ignored_even_unsigned(world):
    receive(event(), signature="", connection_id=uuid.uuid4())
    world["connection"].provider = "workable"
    receive(event(), signature="")

    assert world["sent"] == []


def test_a_broken_connections_candidate_waits_to_be_invited_once_reconnected(world):
    world["connection"].status = "broken"

    with pytest.raises(HTTPException) as refused:
        receive(event(), signature="forged")

    assert refused.value.status_code == 401
    assert world["rows"] == {}

    receive(event())

    assert world["sent"] == []
    assert len(world["rows"]) == 1


def test_the_name_the_ats_sent_goes_with_the_invite(world, companies_api):
    d = json.loads(event())
    d["payload"]["application"]["candidate"].update(first_name="Ann", last_name=" Lee")
    receive(json.dumps(d).encode())

    assert companies_api["names"] == {"ann@example.com": "Ann Lee"}
