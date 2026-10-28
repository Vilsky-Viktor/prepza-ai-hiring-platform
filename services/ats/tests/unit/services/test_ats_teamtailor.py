import asyncio
import json
import uuid

import pytest
from fastapi import HTTPException

from ats.integrations import teamtailor
from ats.models.ats import AtsCandidate, AtsConnection, AtsJobLink
from ats.repositories import ats, ats_candidates, ats_links, ats_results
from ats.services import ats as integrations
from ats.services import ats_candidates as flow
from ats.services import ats_webhooks as hooks
from tests.unit.arrivals import deliver_arrivals
from tests.unit.conftest import interview
from tests.unit.helpers.test_teamtailor_signatures import signature

SECRET = "signature-key"
CONNECTION_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def event(name="job_application.update", application_id=55, wrapped=False) -> bytes:
    found = {"event_name": name, "data": {"id": application_id}}

    return json.dumps({"payload": found} if wrapped else found).encode()


@pytest.fixture
def world(monkeypatch, companies_api):
    """A Teamtailor connection with job 101 linked at stage 7, Teamtailor's application 55 as
    `state["application"]`, the candidate rows in memory, and invites recorded, not sent."""
    connection = AtsConnection(
        id=CONNECTION_ID,
        company_id=uuid.uuid4(),
        provider="teamtailor",
        status="connected",
        created_by="ann",
    )
    companies_api["interviews"][INTERVIEW_ID] = interview(
        connection.company_id, interview_id=INTERVIEW_ID
    )
    state = {
        "connection": connection,
        "key": {"host": "https://api.teamtailor.com", "key": "k", "webhook_secret": SECRET},
        "application": {
            "job_id": "101",
            "stage_id": "7",
            "candidate_id": "44",
            "email": "ann@example.com",
        },
        "read": [],
        "rows": {},
        "linked": True,
        "sent": companies_api["sent"],
    }

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
            stage_id="7",
        )

    async def has_links(connection_id):
        return state["linked"]

    async def key(found):
        return state["key"]

    async def application(host, key, application_id):
        state["read"].append((host, key, application_id))

        return state["application"]

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
    monkeypatch.setattr(ats_links, "has_links", has_links)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(teamtailor, "application", application)
    monkeypatch.setattr(ats_candidates, "add", add)
    monkeypatch.setattr(ats_candidates, "claim", claim)
    monkeypatch.setattr(ats_candidates, "settle", nothing)
    monkeypatch.setattr(flow.outbox_service, "flush_quietly", nothing)
    deliver_arrivals(monkeypatch, state["rows"])

    return state


def receive(body, given=None, connection_id=CONNECTION_ID):
    given = signature(SECRET, body) if given is None else given
    asyncio.run(hooks.receive_teamtailor(connection_id, body, given))


@pytest.mark.parametrize("wrapped", [False, True])
def test_a_candidate_whose_application_is_in_the_linked_stage_is_invited(world, wrapped):
    receive(event(wrapped=wrapped))

    # The application is read from Teamtailor with the key alone, not the web hook's.
    assert world["read"] == [("https://api.teamtailor.com", "k", "55")]
    assert world["sent"] == [("ann@example.com", "ann")]
    # Kept as Teamtailor's candidate id, for the note later.
    assert list(world["rows"]) == ["44"]


def test_a_new_application_made_in_the_linked_stage_counts_too(world):
    receive(event(name="job_application.create"))

    assert world["sent"] == [("ann@example.com", "ann")]


def test_events_before_a_signature_key_is_saved_are_refused(world):
    del world["key"]["webhook_secret"]

    with pytest.raises(HTTPException) as refused:
        receive(event())

    assert refused.value.status_code == 401
    assert world["read"] == [] and world["sent"] == []


def test_an_event_signed_with_another_key_is_refused(world):
    body = event()

    with pytest.raises(HTTPException) as refused:
        receive(body, given=signature("other", body))

    assert refused.value.status_code == 401
    assert world["read"] == [] and world["sent"] == []


def test_other_events_and_events_without_an_application_arent_read(world):
    receive(event(name="candidate.update"))
    receive(event(application_id=None))
    receive(b'{"payload": {"event_name": "job_application.update"}}')

    assert world["read"] == [] and world["sent"] == []


@pytest.mark.parametrize(
    "changed",
    [{"stage_id": "8"}, {"job_id": "202"}, {"job_id": None}, {"email": None}],
)
def test_another_stage_or_job_or_a_candidate_without_email_isnt_invited(world, changed):
    world["application"].update(changed)
    receive(event())

    assert world["sent"] == [] and world["rows"] == {}


def test_without_a_linked_job_teamtailor_isnt_asked(world):
    world["linked"] = False
    receive(event())

    assert world["read"] == [] and world["sent"] == []


def test_teamtailor_busy_answers_the_event_429_to_send_it_later(world, monkeypatch):
    async def busy(host, key, application_id):
        raise HTTPException(429, "Teamtailor didn't answer")

    monkeypatch.setattr(teamtailor, "application", busy)

    with pytest.raises(HTTPException) as answered:
        receive(event())

    assert answered.value.status_code == 429
    assert world["rows"] == {}


def test_an_unknown_or_non_teamtailor_connection_is_ignored_even_unsigned(world):
    receive(event(), given="", connection_id=uuid.uuid4())
    world["connection"].provider = "greenhouse"
    receive(event(), given="")

    assert world["read"] == [] and world["sent"] == []


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
    """A candidate Teamtailor sent who finished, and the notes recorded instead of sent."""
    connection = AtsConnection(
        id=uuid.uuid4(), provider="teamtailor", status="connected", member_id="5"
    )
    row = AtsCandidate(id=uuid.uuid4(), candidate_id="44", invite_id=uuid.uuid4())
    state = {"notes": [], "reported": [], "row": row, "connection": connection}

    async def for_invite(invite_id):
        return row, connection

    async def key(found):
        return {"host": "https://api.teamtailor.com", "key": "k", "webhook_secret": SECRET}

    async def comment(host, key, candidate_id, member, text):
        state["notes"].append((host, key, candidate_id, member, text))

    async def claim_report(row_id, data):
        return True

    async def mark_reported(row_id):
        state["reported"].append(row_id)

    monkeypatch.setattr(ats_results, "for_invite", for_invite)
    monkeypatch.setattr(ats_results, "claim", claim_report)
    monkeypatch.setattr(ats_results, "mark_reported", mark_reported)
    monkeypatch.setattr(integrations, "credentials", key)
    monkeypatch.setattr(teamtailor, "comment", comment)

    return state


def report(state):
    data = {
        "candidate_invite_id": str(state["row"].invite_id),
        "interview_id": str(INTERVIEW_ID),
        "company_id": str(uuid.uuid4()),
        "title": "Accountant",
        "grade": 82,
        "passed": True,
        "flagged": False,
    }
    asyncio.run(flow.report(data))


def test_results_go_back_to_teamtailor_as_a_note_by_the_member(finished):
    report(finished)

    [(host, key, candidate_id, member, text)] = finished["notes"]
    assert (host, key, candidate_id, member) == ("https://api.teamtailor.com", "k", "44", "5")
    assert "Grade: 82% (passed)" in text
    assert finished["reported"] == [finished["row"].id]


def test_without_a_teamtailor_user_to_write_as_nothing_goes_back(finished):
    finished["connection"].member_id = None
    report(finished)

    # Given up: marked, so it isn't tried again.
    assert finished["notes"] == [] and finished["reported"] == [finished["row"].id]


def test_the_name_teamtailor_has_goes_with_the_invite(world, companies_api):
    world["application"]["name"] = "Ann Lee"
    receive(event())

    assert companies_api["names"] == {"ann@example.com": "Ann Lee"}
