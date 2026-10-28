import asyncio
import json
import uuid

import pytest
from fastapi import HTTPException

from ats.integrations import recruitee
from ats.models.ats import AtsCandidate, AtsConnection, AtsJobLink
from ats.repositories import ats, ats_candidates, ats_links, ats_results
from ats.services import ats as integrations
from ats.services import ats_candidates as flow
from ats.services import ats_webhooks as hooks
from tests.unit.arrivals import deliver_arrivals
from tests.unit.conftest import interview
from tests.unit.integrations.test_recruitee import signature

SECRET = "web-hook-secret"
CONNECTION_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def event(
    event_type="candidate_moved",
    subtype="stage_changed",
    offer_id=101,
    stage_id=7,
    emails=("ann@example.com",),
) -> bytes:
    return json.dumps(
        {
            "event_type": event_type,
            "event_subtype": subtype,
            "payload": {
                "candidate": {"id": 44, "emails": list(emails)},
                "offer": {"id": offer_id},
                "details": {"from_stage": {"id": 6}, "to_stage": {"id": stage_id}},
            },
        }
    ).encode()


@pytest.fixture
def world(monkeypatch, companies_api):
    """A Recruitee connection with job 101 linked at stage 7, the candidate rows in memory, and
    invites recorded, not sent."""
    connection = AtsConnection(
        id=CONNECTION_ID,
        company_id=uuid.uuid4(),
        provider="recruitee",
        status="connected",
        created_by="ann",
    )
    companies_api["interviews"][INTERVIEW_ID] = interview(
        connection.company_id, interview_id=INTERVIEW_ID
    )
    state = {
        "connection": connection,
        "key": {"company": "acme", "token": "t", "webhook_secret": SECRET},
        "jobs": [],
        "rows": {},
        "sent": companies_api["sent"],
    }

    async def connection_by_id(connection_id):
        return state["connection"] if connection_id == CONNECTION_ID else None

    async def link_for_job(connection_id, job_id):
        state["jobs"].append(job_id)

        if job_id != "101":
            return None

        return AtsJobLink(
            id=uuid.uuid4(),
            connection_id=connection_id,
            interview_id=INTERVIEW_ID,
            job_id=job_id,
            stage_id="7",
        )

    async def key(found):
        return state["key"]

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


def receive(body, given=None, connection_id=CONNECTION_ID):
    given = signature(SECRET, body) if given is None else given
    asyncio.run(hooks.receive_recruitee(connection_id, body, given))


def test_a_candidate_moved_into_the_linked_stage_is_invited(world):
    receive(event())

    assert world["sent"] == [("ann@example.com", "ann")]
    # Kept as Recruitee's candidate id, for the note later.
    assert list(world["rows"]) == ["44"]


def test_the_first_email_the_candidate_has_is_invited(world):
    receive(event(emails=("", None, "bob@example.com", "ann@example.com")))

    assert world["sent"] == [("bob@example.com", "ann")]


def test_events_before_the_secret_is_saved_are_answered_and_ignored(world):
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
    receive(event(event_type="candidate_created"))
    receive(event(subtype="disqualified"))
    receive(event(emails=()))
    receive(event(emails=("",)))

    assert world["jobs"] == [] and world["sent"] == []


@pytest.mark.parametrize(("offer_id", "stage_id"), [(101, 8), (202, 7), (None, 7)])
def test_another_stage_or_job_isnt_invited(world, offer_id, stage_id):
    receive(event(offer_id=offer_id, stage_id=stage_id))

    assert world["sent"] == [] and world["rows"] == {}


def test_an_unknown_or_non_recruitee_connection_is_ignored_even_unsigned(world):
    receive(event(), given="", connection_id=uuid.uuid4())
    world["connection"].provider = "teamtailor"
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


@pytest.fixture
def finished(monkeypatch):
    """A candidate Recruitee sent who finished (no member: notes go as the token's person), and
    the notes recorded instead of sent."""
    connection = AtsConnection(id=uuid.uuid4(), provider="recruitee", status="connected")
    row = AtsCandidate(id=uuid.uuid4(), candidate_id="44", invite_id=uuid.uuid4())
    state = {"notes": [], "reported": [], "row": row}

    async def for_invite(invite_id):
        return row, connection

    async def key(found):
        return {"company": "acme", "token": "t", "webhook_secret": SECRET}

    async def comment(company, token, candidate_id, member, text):
        state["notes"].append((company, token, candidate_id, member, text))

    async def claim_report(row_id, data):
        return True

    async def mark_reported(row_id):
        state["reported"].append(row_id)

    monkeypatch.setattr(ats_results, "for_invite", for_invite)
    monkeypatch.setattr(ats_results, "claim", claim_report)
    monkeypatch.setattr(ats_results, "mark_reported", mark_reported)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(recruitee, "comment", comment)

    return state


def test_results_go_back_to_recruitee_as_a_note_without_a_member(finished):
    data = {
        "candidate_invite_id": str(finished["row"].invite_id),
        "interview_id": str(INTERVIEW_ID),
        "company_id": str(uuid.uuid4()),
        "title": "Accountant",
        "grade": 82,
        "passed": True,
        "flagged": False,
    }
    asyncio.run(flow.report(data))

    [(company, token, candidate_id, member, text)] = finished["notes"]
    assert (company, token, candidate_id, member) == ("acme", "t", "44", None)
    assert "Grade: 82% (passed)" in text
    assert finished["reported"] == [finished["row"].id]


def test_the_name_the_ats_sent_goes_with_the_invite(world, companies_api):
    d = json.loads(event())
    d["payload"]["candidate"]["name"] = " Ann Lee "
    receive(json.dumps(d).encode())

    assert companies_api["names"] == {"ann@example.com": "Ann Lee"}
