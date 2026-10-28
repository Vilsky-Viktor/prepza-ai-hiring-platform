import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.constants.invites import InviteStatus
from companies.integrations import rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import candidates, companies
from tests.unit import fake_candidates

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
INVITE_ID = uuid.uuid4()
URL = f"/companies/{COMPANY_ID}/candidates"


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


@pytest.fixture
def asked(monkeypatch):
    """A company with a viewer, bob, and one finished candidate in its Backend interview; what
    storage's page was asked for."""
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="viewer")
    ]
    interview = Interview(id=INTERVIEW_ID, company_id=COMPANY_ID, title="Backend", pass_mark=70)
    invite = CandidateInvite(
        id=INVITE_ID,
        interview_id=INTERVIEW_ID,
        email="ann@example.com",
        status=InviteStatus.FINISHED,
        grade=80,
        flagged=True,
        created_at=datetime.now(UTC),
    )
    pages = []

    async def fake_company(session, _company_id):
        return company

    async def fake_page(session, company_id, offset, limit, q, email=""):
        pages.append((company_id, offset, limit, q))

        return [(invite, interview)]

    async def fake_scores(_invite_ids):
        return {str(INVITE_ID): {"progress": 100, "grade": 80, "finished": True, "copies": 2}}

    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(candidates, "company_page", fake_page)
    monkeypatch.setattr(rounds, "invite_scores", fake_scores)

    return pages


def test_a_viewer_finds_candidates_across_the_companys_interviews(client, asked):
    sign_in("bob")
    response = client.get(URL, params={"q": " ANN ", "offset": 20, "limit": 10})
    row = response.json()[0]

    assert response.status_code == 200
    assert asked == [(COMPANY_ID, 20, 10, "ANN")]
    assert (row["interview_id"], row["interview_title"], row["id"], row["email"]) == (
        str(INTERVIEW_ID),
        "Backend",
        str(INVITE_ID),
        "ann@example.com",
    )
    assert (row["status"], row["grade"], row["passed"], row["progress"], row["copies"]) == (
        "finished",
        80,
        True,
        100,
        2,
    )
    # The stored results already match rounds': nothing to store.
    assert fake_candidates.SAVED == []


def test_an_outsider_finds_no_company(client, asked):
    sign_in("mallory")

    assert client.get(URL).status_code == 404
    assert asked == []


def test_a_search_longer_than_an_email_is_refused(client, asked):
    sign_in("bob")

    assert client.get(URL, params={"q": "a" * 255}).status_code == 422
