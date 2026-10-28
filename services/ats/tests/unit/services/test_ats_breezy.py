import asyncio
import json
import uuid

import pytest
from fastapi import HTTPException

from ats.integrations import breezy
from ats.integrations.errors import KeyRejected
from ats.models.ats import AtsCandidate, AtsConnection, AtsJobLink
from ats.repositories import ats, ats_candidates, ats_links, ats_results
from ats.services import ats as integrations
from ats.services import ats_candidates as flow
from ats.services import ats_webhooks as hooks
from ats.services import reports
from tests.unit.arrivals import deliver_arrivals
from tests.unit.conftest import interview
from tests.unit.integrations.test_breezy import signature

SECRET = "web-hook-secret"
CONNECTION_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def event(
    event_type="candidateStatusUpdated",
    position_id="p1",
    stage_id="s7",
    email="ann@example.com",
) -> bytes:
    return json.dumps(
        {
            "type": event_type,
            "object": {
                "candidate": {"_id": "cand1", "email_address": email},
                "position": {"_id": position_id},
                "stage": {"id": stage_id},
            },
        }
    ).encode()


@pytest.fixture
def world(monkeypatch, companies_api):
    """A Breezy HR connection with position p1 linked at stage s7, the candidate rows in memory,
    and invites recorded, not sent."""
    connection = AtsConnection(
        id=CONNECTION_ID,
        company_id=uuid.uuid4(),
        provider="breezy",
        status="connected",
        created_by="ann",
    )
    companies_api["interviews"][INTERVIEW_ID] = interview(
        connection.company_id, interview_id=INTERVIEW_ID
    )
    state = {
        "connection": connection,
        "key": {"company": "c1", "token": "t", "webhook_id": "w1", "webhook_secret": SECRET},
        "jobs": [],
        "rows": {},
        "deleted": [],
        "sent": companies_api["sent"],
    }

    async def connection_by_id(session, connection_id):
        return state["connection"] if connection_id == CONNECTION_ID else None

    async def link_for_job(session, connection_id, job_id):
        state["jobs"].append(job_id)

        if job_id != "p1":
            return None

        return AtsJobLink(
            id=uuid.uuid4(),
            connection_id=connection_id,
            interview_id=INTERVIEW_ID,
            job_id=job_id,
            stage_id="s7",
        )

    async def key(found):
        return state["key"]

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
            ),
        )

    async def claim(session, row_id, statuses):
        return True

    async def nothing(*args, **kwargs):
        return None

    async def unsubscribe(company, token, endpoint_id):
        state["deleted"].append((company, token, endpoint_id))

    monkeypatch.setattr(ats, "connection_by_id", connection_by_id)
    monkeypatch.setattr(ats_links, "link_for_job", link_for_job)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(ats_candidates, "add", add)
    monkeypatch.setattr(ats_candidates, "claim", claim)
    monkeypatch.setattr(ats_candidates, "settle", nothing)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", nothing)
    deliver_arrivals(monkeypatch, state["rows"])
    monkeypatch.setattr(breezy, "unsubscribe", unsubscribe)

    return state


def receive(body, given=None, connection_id=CONNECTION_ID):
    given = signature(SECRET, body) if given is None else given
    asyncio.run(hooks.receive_breezy(connection_id, body, given))


def test_a_candidate_moved_into_the_linked_stage_is_invited(world):
    receive(event())

    assert world["sent"] == [("ann@example.com", "ann")]
    # Kept as "<position>:<candidate>", where the note goes later.
    assert list(world["rows"]) == ["p1:cand1"]


def test_events_without_a_secret_are_answered_and_ignored(world):
    del world["key"]["webhook_secret"]
    receive(event(), given="")

    assert world["jobs"] == [] and world["sent"] == []


def test_an_event_signed_with_another_secret_is_refused(world):
    body = event()

    with pytest.raises(HTTPException) as refused:
        receive(body, given=signature("other", body))

    assert refused.value.status_code == 401
    assert world["jobs"] == [] and world["sent"] == []


def test_other_events_and_candidates_without_an_email_are_ignored(world):
    receive(event(event_type="candidateAdded"))
    receive(event(email=None))
    receive(event(email=""))

    assert world["jobs"] == [] and world["sent"] == []


@pytest.mark.parametrize(("position_id", "stage_id"), [("p1", "s8"), ("p2", "s7"), (None, "s7")])
def test_another_stage_or_position_isnt_invited(world, position_id, stage_id):
    receive(event(position_id=position_id, stage_id=stage_id))

    assert world["sent"] == [] and world["rows"] == {}


def test_an_unknown_or_non_breezy_connection_is_ignored_even_unsigned(world):
    receive(event(), given="", connection_id=uuid.uuid4())
    world["connection"].provider = "recruitee"
    receive(event(), given="")

    assert world["jobs"] == [] and world["sent"] == []


def test_a_broken_connections_candidate_waits_to_be_invited_once_reconnected(world):
    world["connection"].status = "broken"

    with pytest.raises(HTTPException) as refused:
        receive(event(), given="forged")

    assert refused.value.status_code == 401
    assert world["rows"] == {}

    receive(event())

    assert world["sent"] == []
    assert len(world["rows"]) == 1


def test_removing_the_web_hook_deletes_it_in_breezy(world):
    asyncio.run(integrations.remove_webhook(world["connection"]))

    assert world["deleted"] == [("c1", "t", "w1")]


def test_only_a_breezy_connection_with_a_web_hook_has_one_to_remove(world):
    del world["key"]["webhook_id"]
    asyncio.run(integrations.remove_webhook(world["connection"]))
    world["connection"].provider = "recruitee"
    world["key"]["webhook_id"] = "w1"
    asyncio.run(integrations.remove_webhook(world["connection"]))

    assert world["deleted"] == []


@pytest.mark.parametrize("failure", [KeyRejected(), HTTPException(502)])
def test_a_web_hook_breezy_wont_delete_is_left_quietly(world, monkeypatch, failure):
    async def refuse(company, token, endpoint_id):
        raise failure

    monkeypatch.setattr(breezy, "unsubscribe", refuse)

    asyncio.run(integrations.remove_webhook(world["connection"]))


def test_a_key_that_cant_be_read_doesnt_stop_removing_a_connection(world, monkeypatch):
    async def unreadable(found):
        raise HTTPException(409)

    monkeypatch.setattr(integrations, "credentials", unreadable)

    asyncio.run(integrations.remove_webhook(world["connection"]))
    world["connection"].provider = "workable"
    asyncio.run(integrations.remove_webhook(world["connection"]))


@pytest.fixture
def finished(monkeypatch):
    """A candidate Breezy sent who finished, and the notes recorded instead of sent."""
    connection = AtsConnection(id=uuid.uuid4(), provider="breezy", status="connected")
    row = AtsCandidate(id=uuid.uuid4(), candidate_id="p1:cand1", invite_id=uuid.uuid4())
    state = {"notes": [], "reported": [], "row": row}

    async def for_invite(session, invite_id):
        return row, connection

    async def key(found):
        return {"company": "c1", "token": "t", "webhook_secret": SECRET}

    async def comment(company, token, candidate_id, member, text):
        state["notes"].append((company, token, candidate_id, member, text))

    async def claim_report(session, row_id, data):
        return True

    async def mark_reported(session, row_id):
        state["reported"].append(row_id)

    monkeypatch.setattr(ats_results, "for_invite", for_invite)
    monkeypatch.setattr(ats_results, "claim", claim_report)
    monkeypatch.setattr(ats_results, "mark_reported", mark_reported)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(breezy, "comment", comment)

    return state


def test_results_go_back_to_breezy_as_a_note_without_a_member(finished):
    data = {
        "candidate_invite_id": str(finished["row"].invite_id),
        "interview_id": str(INTERVIEW_ID),
        "company_id": str(uuid.uuid4()),
        "title": "Accountant",
        "grade": 82,
        "passed": True,
        "flagged": False,
    }
    asyncio.run(reports.report(data))

    [(company, token, candidate_id, member, text)] = finished["notes"]
    assert (company, token, candidate_id, member) == ("c1", "t", "p1:cand1", None)
    assert "Grade: 82% (passed)" in text
    assert finished["reported"] == [finished["row"].id]


def test_the_name_the_ats_sent_goes_with_the_invite(world, companies_api):
    d = json.loads(event())
    d["object"]["candidate"]["name"] = " Ann Lee "
    receive(json.dumps(d).encode())

    assert companies_api["names"] == {"ann@example.com": "Ann Lee"}
