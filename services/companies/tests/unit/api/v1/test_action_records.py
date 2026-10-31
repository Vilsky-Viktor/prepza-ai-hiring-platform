"""Actions recorded in the company's action log by routes that have no test of their own for it:
renaming an interview and its shareable link (billing logs the automatic top-up itself)."""

import uuid
from datetime import UTC, datetime

import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.events.audit_actions import AuditAction, TargetKind

from companies.integrations import library
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import companies, interviews
from companies.services import interview_changes

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


@pytest.fixture(autouse=True)
def company(monkeypatch):
    """Acme, with Ann its owner and Vic a viewer, and its interview "Backend"; signed in as
    Ann."""
    acme = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    acme.members = [
        Member(company_id=COMPANY_ID, user_id="ann", invited_email="ann@x.com", role="owner"),
        Member(company_id=COMPANY_ID, user_id="vic", invited_email="vic@x.com", role="viewer"),
    ]
    interview = Interview(
        id=INTERVIEW_ID, company_id=COMPANY_ID, title="Backend", set_id=uuid.uuid4()
    )

    async def get_company(session, _id):
        return acme

    async def get_interview(session, _id):
        return interview

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(interviews, "get", get_interview)

    for module, name in (
        (library, "rename_set"),
        (interviews, "set_title"),
        (interviews, "set_link"),
        (interview_changes, "ready_for_invites"),
    ):
        monkeypatch.setattr(module, name, nothing)

    sign_in("ann")

    yield

    app.dependency_overrides.clear()


def interview_action(action):
    return (COMPANY_ID, "ann", action, INTERVIEW_ID, TargetKind.INTERVIEW)


def test_renaming_an_interview_is_recorded(client, audited):
    response = client.patch(f"/interviews/{INTERVIEW_ID}/title", json={"title": "Backend II"})

    assert response.status_code == 204
    assert audited == [interview_action(AuditAction.INTERVIEW_RENAMED)]


def test_turning_the_link_on_and_off_is_recorded(client, audited):
    url = f"/interviews/{INTERVIEW_ID}/link"

    assert client.put(url, json={"on": True}).status_code == 200
    assert client.put(url, json={"on": False}).status_code == 200
    assert audited == [
        interview_action(AuditAction.LINK_TURNED_ON),
        interview_action(AuditAction.LINK_TURNED_OFF),
    ]


def test_a_viewer_changes_nothing_and_nothing_is_recorded(client, audited):
    sign_in("vic")

    assert (
        client.patch(f"/interviews/{INTERVIEW_ID}/title", json={"title": "Backend II"}).status_code
        == 403
    )
    assert client.put(f"/interviews/{INTERVIEW_ID}/link", json={"on": True}).status_code == 403
    assert audited == []
