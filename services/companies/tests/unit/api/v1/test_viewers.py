import uuid
from datetime import UTC, datetime

import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User

from companies.api.v1 import companies as companies_route
from companies.constants.roles import Role
from companies.integrations import billing, library
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, credit_invites, interviews, invites, members
from companies.services import set_cache
from companies.services.access import can_edit, is_owner
from tests.unit import fake_candidates

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
INVITE_ID = uuid.uuid4()
TOPIC_ID = uuid.uuid4()
QUESTION_ID = uuid.uuid4()
INTERVIEW = f"/interviews/{INTERVIEW_ID}"
CANDIDATE = f"{INTERVIEW}/candidates/{INVITE_ID}"
COMPANY = f"/companies/{COMPANY_ID}"

# Every route that changes the company, its tests or candidates, or spends credits.
FORBIDDEN = [
    ("post", f"/interviews?company_id={COMPANY_ID}", {"text": "A Python developer"}),
    ("post", f"/interviews/from-template?company_id={COMPANY_ID}", {"template_id": str(TOPIC_ID)}),
    ("patch", f"{INTERVIEW}/settings", {"hired": True}),
    ("patch", f"{INTERVIEW}/settings", {"keep_private": True}),
    ("patch", f"{INTERVIEW}/title", {"title": "New title"}),
    ("delete", INTERVIEW, None),
    ("put", f"{INTERVIEW}/topics/{TOPIC_ID}/limit", {"limit": 1}),
    ("post", f"{INTERVIEW}/questions/{QUESTION_ID}/regenerate", None),
    ("post", f"{INTERVIEW}/questions/{QUESTION_ID}/wrong", None),
    ("post", f"{INTERVIEW}/generation/review", {"selected": [0]}),
    ("post", f"{INTERVIEW}/generation/retry", None),
    ("post", f"{INTERVIEW}/generation/cancel", None),
    ("post", f"{INTERVIEW}/candidates", {"email": "cid@example.com"}),
    ("post", f"{INTERVIEW}/candidates/bulk", {"text": "cid@example.com"}),
    ("delete", CANDIDATE, None),
    ("put", f"{CANDIDATE}/extra-time", {"extra_time": 25}),
    ("put", f"{INTERVIEW}/link", {"on": True}),
    ("patch", f"{COMPANY}/name", {"title": "New name"}),
    ("put", f"{COMPANY}/logo", {"image": "aGVsbG8="}),
    ("delete", f"{COMPANY}/logo", None),
    ("put", f"{COMPANY}/website", {"website": "example.com"}),
    ("post", f"/members?company_id={COMPANY_ID}", {"email": "cid@example.com"}),
]


@pytest.fixture
def viewer(monkeypatch):
    """Bob is a viewer of a company with one generated test and one invited candidate."""
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    company = Company(
        id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC), verification_status="none"
    )
    company.members = [
        Member(
            id=uuid.uuid4(),
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role=Role.VIEWER,
            created_at=datetime.now(UTC),
        )
    ]
    interview = Interview(
        id=INTERVIEW_ID, company_id=COMPANY_ID, generation_id=uuid.uuid4(), set_id=uuid.uuid4()
    )
    invite = CandidateInvite(
        id=INVITE_ID, interview_id=INTERVIEW_ID, email="cid@example.com", status="invited"
    )
    fake_candidates.add(invite)

    async def fake_company(session, _company_id):
        return company

    async def fake_interview(session, _interview_id):
        return interview

    async def fake_invite(session, _invite_id):
        return invite

    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(invites, "get", fake_invite)
    yield company
    app.dependency_overrides.clear()


@pytest.mark.parametrize(("method", "url", "body"), FORBIDDEN)
def test_a_viewer_changes_nothing(client, viewer, method, url, body):
    response = client.request(method.upper(), url, json=body)

    assert response.status_code == 403


def test_a_viewer_reads_the_company_without_verifying_it(client, viewer, monkeypatch):
    verified = []

    async def fake_counts(session, company_ids):
        return {}

    async def fake_verify(company, user):
        verified.append(user.uid)

    async def fake_credits(company_id):
        return {"available": 900, "low": False, "candidates": 3}

    async def fake_list(session, company_id, offset, limit):
        return viewer.members

    async def fake_holding(session, company_id):
        return 0

    monkeypatch.setattr(interviews, "counts", fake_counts)
    monkeypatch.setattr(companies_route, "verify_by_email", fake_verify)
    monkeypatch.setattr(billing, "company_credits", fake_credits)
    monkeypatch.setattr(credit_invites, "count_holding", fake_holding)
    monkeypatch.setattr(members, "list_for_company", fake_list)

    company = client.get(COMPANY)

    assert company.status_code == 200
    assert (company.json()["role"], company.json()["can_edit"]) == ("viewer", False)
    assert (company.json()["can_delete"], company.json()["can_manage_members"]) == (False, False)
    assert verified == []
    credits = client.get(f"{COMPANY}/credits")
    assert credits.status_code == 200
    assert credits.json()["candidates"] == 3
    assert client.get(f"/members?company_id={COMPANY_ID}").status_code == 200


def test_a_viewer_reads_questions(client, viewer, monkeypatch):
    async def fake_questions(set_id, topic_id):
        return []

    monkeypatch.setattr(library, "get_topic_questions", fake_questions)

    assert client.get(f"{INTERVIEW}/topics/{TOPIC_ID}/questions").status_code == 200


def test_a_viewer_reads_an_interview_with_the_language_it_is_written_in(
    client, viewer, monkeypatch
):
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
        generation_failed=False,
        title="Backend",
        question_seconds=60,
        hired=False,
        keep_private=False,
        pass_mark=70,
        language="ar",
        created_at=datetime.now(UTC),
    )

    async def fake_interview(session, _interview_id):
        return interview

    async def no_set(_set_id):
        return None

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(set_cache, "get_set", no_set)

    response = client.get(INTERVIEW)

    assert response.status_code == 200
    # Its topics and questions carry it on the page (lang, dir).
    assert response.json()["language"] == "ar"


@pytest.mark.parametrize(
    ("role", "editor"), [(Role.OWNER, True), (Role.ADMIN, True), (Role.VIEWER, False)]
)
def test_only_owners_and_admins_edit(role, editor):
    assert can_edit(Member(role=role)) is editor


@pytest.mark.parametrize(
    ("role", "owner"), [(Role.OWNER, True), (Role.ADMIN, False), (Role.VIEWER, False)]
)
def test_only_the_owner_is_the_owner(role, owner):
    assert is_owner(Member(role=role)) is owner
