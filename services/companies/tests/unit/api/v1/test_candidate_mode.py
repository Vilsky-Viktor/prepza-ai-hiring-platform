import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.invites import InviteStatus
from companies.helpers.candidates import takes_voice, voice_override
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import candidates, companies, interviews, invites
from tests.unit.api.v1.test_candidate_invites import URL, invite_setup

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


@pytest.fixture
def candidate(monkeypatch):
    """Ann, invited to a click-mode interview in English, as Bob (an admin) sees her."""
    interview = Interview(
        id=INTERVIEW_ID, company_id=COMPANY_ID, question_seconds=60, language="en", voice=False
    )
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="admin")
    ]
    invite = CandidateInvite(id=uuid.uuid4(), interview_id=INTERVIEW_ID, email="ann@example.com")
    invite.status = InviteStatus.INVITED
    saved = []

    async def fake_interview(session, _id):
        return interview

    async def fake_company(session, _id):
        return company

    async def fake_invite(session, interview_id, invite_id):
        return invite if invite.interview_id == interview_id else None

    async def fake_change(session, invite_id, values, statuses):
        saved.append(values)

        return invite.status in statuses

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(candidates, "get", fake_invite)
    monkeypatch.setattr(invites, "change", fake_change)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )

    yield interview, invite, saved

    app.dependency_overrides.clear()


def url(invite):
    return f"/interviews/{INTERVIEW_ID}/candidates/{invite.id}/voice"


@pytest.mark.parametrize(
    ("interview_voice", "own", "voice"),
    [(False, None, False), (True, None, True), (False, True, True), (True, False, False)],
)
def test_a_candidate_takes_their_own_mode_else_the_interviews(interview_voice, own, voice):
    interview = SimpleNamespace(voice=interview_voice)

    assert takes_voice(SimpleNamespace(voice=own), interview) is voice


def test_only_a_mode_apart_from_the_interviews_is_kept():
    click = SimpleNamespace(voice=False)

    assert voice_override(True, click) is True
    # The interview's own mode: they follow the interview's from then on.
    assert voice_override(False, click) is None
    assert voice_override(False, SimpleNamespace(voice=True)) is False


def test_a_company_sets_a_candidates_mode_before_they_start(client, candidate, audited):
    _, invite, saved = candidate

    assert client.put(url(invite), json={"voice": True}).status_code == 204
    # Back to the interview's mode: nothing of their own is kept.
    assert client.put(url(invite), json={"voice": False}).status_code == 204
    assert saved == [{"voice": True}, {"voice": None}]
    assert (
        audited
        == [(COMPANY_ID, "bob", AuditAction.CANDIDATE_MODE_SET, invite.id, TargetKind.CANDIDATE)]
        * 2
    )


def test_a_candidates_mode_is_fixed_once_they_start(client, candidate):
    _, invite, saved = candidate
    invite.status = InviteStatus.IN_PROCESS

    refused = client.put(url(invite), json={"voice": True})

    assert refused.status_code == 409
    assert refused.json() == {
        "detail": "The interview mode can only be changed before the candidate starts.",
        "code": "candidate_started",
    }
    assert saved == []


def test_voice_is_refused_for_a_candidate_in_a_language_voice_mode_doesnt_speak(client, candidate):
    interview, invite, saved = candidate
    interview.language = "ja"

    refused = client.put(url(invite), json={"voice": True})

    assert refused.status_code == 422
    assert refused.json() == {
        "detail": "Voice mode isn't available in this interview's language.",
        "code": "voice_unavailable",
    }
    # Click mode is always there.
    assert client.put(url(invite), json={"voice": False}).status_code == 204
    assert saved == [{"voice": None}]


def test_a_viewer_cant_change_a_candidates_mode(client, candidate):
    _, invite, saved = candidate
    app.dependency_overrides[current_user] = lambda: User(
        uid="vic", email="vic@example.com", email_verified=True
    )

    assert client.put(url(invite), json={"voice": True}).status_code in (403, 404)
    assert saved == []


def mode_setup(monkeypatch, language):
    """invite_setup, the interview in `language` (click mode), and what each save was told of the
    candidate's mode."""
    sent, used = invite_setup(monkeypatch)
    interview = asyncio.run(interviews.get(None, INTERVIEW_ID))
    interview.language = language
    saved = invites.upsert
    modes = []

    async def spy(*args, mode_chosen=False, voice=None, **options):
        modes.append((mode_chosen, voice))

        return await saved(*args, mode_chosen=mode_chosen, voice=voice, **options)

    monkeypatch.setattr(invites, "upsert", spy)

    return sent, used, modes


@pytest.mark.parametrize(
    ("body", "mode"),
    [
        ({}, (False, None)),
        ({"voice": True}, (True, True)),
        # The interview's own mode: nothing of their own is kept.
        ({"voice": False}, (True, None)),
    ],
)
def test_an_invite_chooses_how_the_candidate_takes_it(client, monkeypatch, body, mode):
    _, _, modes = mode_setup(monkeypatch, "en")

    response = client.post(URL, json={"email": "carol@example.com", **body})
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert modes == [mode]


@pytest.mark.parametrize("url", [URL, f"{URL}/bulk"])
def test_voice_is_refused_in_a_language_voice_mode_doesnt_speak(client, monkeypatch, url):
    sent, used, _ = mode_setup(monkeypatch, "ja")
    body = {"voice": True, "email": "carol@example.com", "text": "carol@example.com"}

    response = client.post(url, json=body)
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Voice mode isn't available in this interview's language.",
        "code": "voice_unavailable",
    }
    # Refused before any credits are set aside or email is queued.
    assert (sent, used) == ([], [])
