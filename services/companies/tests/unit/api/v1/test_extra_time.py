import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.service_auth import issue_token
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.invites import InviteStatus
from companies.helpers.candidates import candidate_seconds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import candidates, companies, interviews, invites

SECRET = "test-secret-that-is-at-least-32-bytes"
COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


@pytest.fixture
def candidate(monkeypatch):
    interview = Interview(id=INTERVIEW_ID, company_id=COMPANY_ID, question_seconds=60)
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="admin")
    ]
    invite = CandidateInvite(
        id=uuid.uuid4(), interview_id=INTERVIEW_ID, email="ann@example.com", extra_time=0
    )
    invite.status = InviteStatus.INVITED
    saved = {}

    async def fake_interview(session, _id):
        return interview

    async def fake_company(session, _id):
        return company

    async def fake_invite(session, interview_id, invite_id):
        return invite if invite.interview_id == interview_id else None

    async def fake_change(session, invite_id, values, statuses, unstarted=False):
        saved.update(values)

        return invite.status in statuses

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(candidates, "get", fake_invite)
    monkeypatch.setattr(invites, "change", fake_change)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )

    yield invite, saved

    app.dependency_overrides.clear()


def url(invite):
    return f"/interviews/{INTERVIEW_ID}/candidates/{invite.id}/extra-time"


def test_extra_time_lengthens_each_question():
    assert candidate_seconds(60, 0) == 60
    assert candidate_seconds(60, 50) == 90
    assert candidate_seconds(45, 25) == 56
    assert candidate_seconds(60, None) == 60


def test_a_company_sets_extra_time_before_the_candidate_starts(client, candidate, audited):
    invite, saved = candidate

    assert client.put(url(invite), json={"extra_time": 50}).status_code == 204
    assert saved == {"extra_time": 50}
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.EXTRA_TIME_SET, invite.id, TargetKind.CANDIDATE)
    ]
    # Only the offered amounts.
    assert client.put(url(invite), json={"extra_time": 30}).status_code == 422

    invite.status = InviteStatus.IN_PROCESS

    assert client.put(url(invite), json={"extra_time": 100}).status_code == 409


@pytest.mark.parametrize("via", ["assistant", "mcp"])
def test_extra_time_given_through_the_assistant_or_an_ai_app_is_audited_as_such(
    client, candidate, audited, via
):
    invite, _ = candidate
    header = {"X-Assistant": issue_token(via, "companies", SECRET)}

    assert client.put(url(invite), json={"extra_time": 50}, headers=header).status_code == 204
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.EXTRA_TIME_SET, invite.id, TargetKind.CANDIDATE, via)
    ]
