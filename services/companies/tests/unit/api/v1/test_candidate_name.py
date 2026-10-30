"""A candidate's name: filled once from their verified sign-in as they start, and corrected by the
company's owners and admins."""

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind
from prepza_common.i18n.names import clean_name

from companies.api.v1 import candidates as candidates_router
from companies.constants.invites import MAX_CANDIDATE_NAME_LENGTH, InviteStatus
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, interviews, invite_progress
from companies.repositories import invites as invite_store
from companies.services import candidate_start, interview_access
from companies.services import candidate_start as invites_router
from tests.unit import fake_candidates
from tests.unit.services.test_candidate_start import (  # noqa: F401 (fixture)
    INTERVIEW,
    INVITE,
    steps,
)

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def sign_in(uid, name=None, email=None):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=email or f"{uid}@example.com", email_verified=True, name=name
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_a_clean_name_is_trimmed_cut_and_blank_is_unknown():
    assert clean_name("  Maria Kowalska ") == "Maria Kowalska"
    assert clean_name("x" * (MAX_CANDIDATE_NAME_LENGTH + 5)) == "x" * MAX_CANDIDATE_NAME_LENGTH
    assert clean_name("   ") is None
    assert clean_name(None) is None


def test_starting_passes_the_name_from_the_verified_sign_in(steps, monkeypatch):  # noqa: F811
    started = []

    async def start(session, invite_id, user_id, name=None):
        started.append((user_id, name))

        return "invited"

    monkeypatch.setattr(invite_progress, "start", start)
    user = User(uid="cand", email="cand@example.com", email_verified=True, name=" Maria ")
    asyncio.run(candidate_start.start_sessions(INVITE, INTERVIEW, user))

    assert started == [("cand", "Maria")]


def test_a_name_sent_in_the_body_of_a_start_is_ignored(client, monkeypatch):
    invite = CandidateInvite(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email="maria@example.com",
        token="token-1",
        status=InviteStatus.IN_PROCESS,
    )
    interview = Interview(id=INTERVIEW_ID, company_id=COMPANY_ID, set_id=uuid.uuid4())
    users = []

    async def fake_get(session, token):
        return invite, interview

    async def fake_start(invite, interview, user):
        users.append(user)

        return {"sessions": []}

    monkeypatch.setattr(invite_store, "get_by_token", fake_get)
    monkeypatch.setattr(invites_router, "start_sessions", fake_start)
    sign_in("maria", "Maria Kowalska", "maria@example.com")
    response = client.post("/invites/token-1/start", json={"name": "Mallory"})

    assert response.status_code == 200
    assert [user.name for user in users] == ["Maria Kowalska"]


@pytest.fixture
def candidate(monkeypatch):
    interview = Interview(id=INTERVIEW_ID, company_id=COMPANY_ID)
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id=uid, invited_email=f"{uid}@example.com", role=role)
        for uid, role in (("olga", "owner"), ("adam", "admin"), ("vera", "viewer"))
    ]
    invite = CandidateInvite(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email="maria@example.com",
        status=InviteStatus.IN_PROCESS,
        name="mk",
    )
    fake_candidates.add(invite)
    saved = []

    async def fake_interview(session, _id):
        return interview

    async def fake_company(session, _id):
        return company

    async def change(session, invite_id, values, statuses, unstarted=False):
        saved.append((invite_id, values["name"]))

        return invite.status in statuses

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(invite_store, "change", change)

    return invite, saved


def url(invite):
    return f"/interviews/{INTERVIEW_ID}/candidates/{invite.id}/name"


@pytest.mark.parametrize("uid", ["olga", "adam"])
def test_owners_and_admins_correct_a_candidates_name_trimmed(client, candidate, uid, audited):
    invite, saved = candidate
    sign_in(uid)

    assert client.patch(url(invite), json={"name": "  Maria Kowalska "}).status_code == 204
    assert saved == [(invite.id, "Maria Kowalska")]
    assert [event[1:] for event in audited] == [
        (uid, AuditAction.CANDIDATE_RENAMED, invite.id, TargetKind.CANDIDATE)
    ]


def test_a_blank_name_makes_it_unknown_again(client, candidate):
    invite, saved = candidate
    sign_in("olga")

    assert client.patch(url(invite), json={"name": "   "}).status_code == 204
    assert saved == [(invite.id, None)]


@pytest.mark.parametrize("uid", ["vera", "stranger"])
def test_viewers_and_outsiders_cant_rename_a_candidate(client, candidate, uid, audited):
    invite, saved = candidate
    sign_in(uid)

    assert client.patch(url(invite), json={"name": "Maria"}).status_code in (403, 404)
    assert saved == [] and audited == []


def test_a_too_long_name_is_refused(client, candidate):
    invite, saved = candidate
    sign_in("olga")
    name = "x" * (MAX_CANDIDATE_NAME_LENGTH + 1)

    assert client.patch(url(invite), json={"name": name}).status_code == 422
    assert saved == []


def test_a_deleted_candidate_cant_be_renamed(client, candidate):
    invite, saved = candidate
    invite.status = InviteStatus.DELETED
    sign_in("olga")

    assert client.patch(url(invite), json={"name": "Maria"}).status_code == 404
    assert saved == []


@pytest.mark.parametrize(
    ("earlier", "code"),
    # Sent again while still open, nothing new is made; an expired invite comes back to life.
    [(None, 201), ("invited", 200), ("in_process", 200), ("expired", 201)],
)
def test_a_single_invite_passes_its_name(client, candidate, monkeypatch, earlier, code):
    names = []

    async def held(session, interview_id, email):
        return earlier, None

    async def invite(interview, company, user, email, name=None, voice=None):
        names.append(name)

        return CandidateInvite(
            id=uuid.uuid4(), email=email, name=name, status="invited", created_at=datetime.now(UTC)
        )

    monkeypatch.setattr(candidates_router.candidate_invites, "invite", invite)
    monkeypatch.setattr(invite_store, "held", held)
    monkeypatch.setattr(interview_access, "attach_set", fake_attach)
    monkeypatch.setattr(interview_access, "refuse_if_paused", nothing)
    monkeypatch.setattr(candidates_router.outbox_service, "flush_quietly", nothing)
    sign_in("olga")
    body = {"email": "ann@example.com", "name": "Ann Lee"}
    response = client.post(f"/interviews/{INTERVIEW_ID}/candidates", json=body)

    assert response.status_code == code
    assert names == ["Ann Lee"]
    assert response.json()["name"] == "Ann Lee"


async def fake_attach(interview):
    interview.set_id = uuid.uuid4()

    return interview


async def nothing(*args):
    return None
