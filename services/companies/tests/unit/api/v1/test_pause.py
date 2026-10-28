import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.config.constants import PAUSED

from companies.api.v1 import pause as pause_routes
from companies.constants.invites import InviteStatus
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, interviews, invites, link_invites
from companies.schemas.invites import InviteStartOut
from companies.services import candidate_start as invite_routes
from companies.services import link_start

INTERVIEW = Interview(
    id=uuid.uuid4(), company_id=uuid.uuid4(), set_id=uuid.uuid4(), question_seconds=60
)


@pytest.fixture(autouse=True)
def paused(monkeypatch):
    """The switch on, and a verified candidate signed in."""

    async def on(redis):
        return True

    monkeypatch.setattr("prepza_common.limits.pause.is_paused", on)
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="cand",
        email="cand@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def started(monkeypatch):
    """Invites and links that would start; returns the starts that went through."""
    calls = []

    async def start(invite, interview, user_id):
        calls.append(invite)

        return InviteStartOut(sessions=[])

    monkeypatch.setattr(invite_routes, "start_sessions", start)
    monkeypatch.setattr(link_start, "start_sessions", start)

    return calls


def stored_invite(monkeypatch, status):
    invite = CandidateInvite(
        id=uuid.uuid4(),
        interview_id=INTERVIEW.id,
        email="cand@example.com",
        token="t",
        status=status,
        created_at=datetime.now(UTC),
    )

    async def get_by_token(session, token):
        return invite, INTERVIEW

    monkeypatch.setattr(invites, "get_by_token", get_by_token)


def linked(monkeypatch, status):
    async def get_by_link(session, token):
        return INTERVIEW

    async def held(session, interview_id, email):
        return status, None

    async def for_link(session, interview_id, email, hold_key=None, details=None):
        return SimpleNamespace(email=email, hold_key=hold_key)

    monkeypatch.setattr(interviews, "get_by_link", get_by_link)
    monkeypatch.setattr(invites, "held", held)
    monkeypatch.setattr(link_invites, "for_link", for_link)


def test_paused_no_candidate_starts_by_invite_but_one_in_the_interview_continues(
    client, monkeypatch, started
):
    stored_invite(monkeypatch, InviteStatus.INVITED)
    refused = client.post("/invites/t/start", json={"pledged": True})

    assert refused.status_code == 503
    assert refused.json()["detail"] == PAUSED

    stored_invite(monkeypatch, InviteStatus.IN_PROCESS)

    assert client.post("/invites/t/start", json={"pledged": True}).status_code == 200
    assert len(started) == 1


def test_paused_no_candidate_starts_by_link_but_one_in_the_interview_continues(
    client, monkeypatch, started
):
    linked(monkeypatch, None)

    assert client.post("/links/abc/start", json={"pledged": True}).status_code == 503

    linked(monkeypatch, InviteStatus.IN_PROCESS)

    assert client.post("/links/abc/start", json={"pledged": True}).status_code == 200
    assert len(started) == 1


@pytest.mark.parametrize(
    "path",
    [
        f"/interviews?company_id={uuid.uuid4()}",
        f"/interviews/{uuid.uuid4()}/preview",
        f"/interviews/{uuid.uuid4()}/generation/review",
        f"/interviews/{uuid.uuid4()}/generation/retry",
        f"/interviews/{uuid.uuid4()}/questions/{uuid.uuid4()}/regenerate",
    ],
)
def test_paused_previews_generations_and_regenerations_are_refused(
    client, monkeypatch, limit_hits, path
):
    """The signed-in candidate owns the interview's company here: the routes that check the
    pause after the interview (to record whose refusal it was) get that far."""
    company = Company(id=INTERVIEW.company_id, name="Acme", created_at=datetime.now(UTC))
    company.members = [Member(company_id=company.id, user_id="cand", role="owner")]
    generated = Interview(
        id=INTERVIEW.id, company_id=company.id, generation_id=uuid.uuid4(), set_id=uuid.uuid4()
    )

    async def get_interview(session, _interview_id):
        return generated

    async def get_company(session, _company_id):
        return company

    monkeypatch.setattr(interviews, "get", get_interview)
    monkeypatch.setattr(companies, "get", get_company)
    body = {"text": "Backend developer", "selected": [0]}
    refused = client.post(path, json=body)

    assert refused.status_code == 503
    assert refused.json()["detail"] == PAUSED
    assert [(hit["limit"], hit["user_id"]) for hit in limit_hits] == [("PAUSED", "cand")]


def test_anyone_reads_the_switch_and_only_a_superadmin_turns_it(client, monkeypatch):
    switched = []

    async def on(redis):
        return True

    async def turn(redis, paused, user_id):
        switched.append((paused, user_id))

    monkeypatch.setattr(pause_routes, "is_paused", on)
    monkeypatch.setattr(pause_routes, "set_paused", turn)

    assert client.get("/pause").json() == {"paused": True}
    assert client.put("/superadmin/pause", json={"paused": False}).status_code == 404

    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    assert client.put("/superadmin/pause", json={"paused": False}).json() == {"paused": False}
    assert switched == [(False, "ann")]


def test_paused_no_invite_goes_out_alone_in_a_list_or_again(client, monkeypatch):
    from tests.unit.api.v1.test_candidate_invites import INTERVIEW_ID, invite_setup

    sent, _ = invite_setup(monkeypatch)
    single = client.post(
        f"/interviews/{INTERVIEW_ID}/candidates", json={"email": "carol@example.com"}
    )
    bulk = client.post(
        f"/interviews/{INTERVIEW_ID}/candidates/bulk", json={"text": "ann@example.com"}
    )

    # Sending an invite again is the same request as sending it.
    assert (single.status_code, bulk.status_code) == (503, 503)
    assert single.json()["detail"] == bulk.json()["detail"] == PAUSED
    assert sent == []


def test_paused_no_reminder_goes_out(client, monkeypatch):
    from companies.api.v1 import schedules

    async def remind():
        raise AssertionError("must not remind while paused")

    monkeypatch.setattr(schedules, "remind_unstarted", remind)

    assert client.post("/internal/schedules/invite-reminders").status_code == 204
