import uuid
from datetime import UTC, datetime

import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User

from companies.constants.invites import MAX_COMPANY_NAME_LENGTH
from companies.constants.roles import EDITORS
from companies.integrations import billing
from companies.main import app
from companies.models.companies import Company, Member
from companies.repositories import companies, interviews

OWNED_ID = uuid.uuid4()
JOINED_ID = uuid.uuid4()


def sign_in(email="bob@example.com", uid="bob", verified=True):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=email, email_verified=verified, name="Bob"
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def company(company_id, name, role):
    item = Company(
        id=company_id, name=name, created_at=datetime.now(UTC), verification_status="none"
    )
    item.members = [
        Member(
            company_id=company_id,
            user_id="bob",
            invited_email="bob@example.com",
            role=role,
            created_at=datetime.now(UTC),
        )
    ]

    return item


@pytest.fixture
def two_companies(monkeypatch):
    owned = company(OWNED_ID, "My company", "owner")
    # A pending invite counts in the team, as the Team page lists it.
    owned.members.append(
        Member(
            company_id=OWNED_ID,
            invited_email="ann@example.com",
            role="viewer",
            created_at=datetime.now(UTC),
        )
    )
    joined = company(JOINED_ID, "Arcolabs", "admin")

    async def fake_list(session, user_id, offset, limit, roles=None, only=None):
        return [owned, joined]

    async def fake_get(session, company_id):
        if company_id == OWNED_ID:
            return owned

        if company_id == JOINED_ID:
            return joined

        return None

    async def fake_counts(session, company_ids):
        return {OWNED_ID: 3}

    monkeypatch.setattr(companies, "list_for_user", fake_list)
    monkeypatch.setattr(companies, "get", fake_get)
    monkeypatch.setattr(interviews, "counts", fake_counts)


def test_lists_every_membership(client, two_companies):
    sign_in()
    response = client.get("/companies")

    assert response.status_code == 200
    assert [
        (row["name"], row["role"], row["interview_count"], row["member_count"])
        for row in response.json()
    ] == [
        ("My company", "owner", 3, 2),
        ("Arcolabs", "admin", 0, 1),
    ]


def test_only_the_owner_may_delete_the_company_and_manage_its_members(client, two_companies):
    sign_in()
    response = client.get("/companies")

    assert [
        (row["name"], row["can_delete"], row["can_manage_members"]) for row in response.json()
    ] == [("My company", True, True), ("Arcolabs", False, False)]


def test_opens_joined_company(client, two_companies):
    sign_in()
    response = client.get(f"/companies/{JOINED_ID}")

    assert response.status_code == 200
    assert response.json()["name"] == "Arcolabs"
    assert response.json()["role"] == "admin"


def test_unknown_company_is_hidden(client, two_companies):
    sign_in()

    assert client.get(f"/companies/{uuid.uuid4()}").status_code == 404


def test_owner_removes_company(client, two_companies, monkeypatch):
    removed = []

    async def fake_delete(session, company_id):
        removed.append(company_id)

    async def no_interviews(session, _company_id, after, limit):
        return []

    monkeypatch.setattr(companies, "delete", fake_delete)
    monkeypatch.setattr(interviews, "page_by_id", no_interviews)
    sign_in()
    response = client.delete(f"/companies/{OWNED_ID}")

    assert response.status_code == 204
    assert removed == [OWNED_ID]


def test_admin_cannot_remove_company(client, two_companies):
    sign_in()

    assert client.delete(f"/companies/{JOINED_ID}").status_code == 403


def test_lists_the_users_companies_with_their_credits(client, monkeypatch):
    company = Company(id=uuid.uuid4(), name="Acme", created_at=datetime.now(UTC), members=[])

    asked = []

    async def mine(session, user_id, offset, limit, roles, only=None):
        asked.append(roles)

        return [company]

    async def credits(company_ids):
        return {
            str(company.id): {"balance": 1_400, "reserved": 200, "available": 1_200, "low": False}
        }

    monkeypatch.setattr(companies, "list_for_user", mine)
    monkeypatch.setattr(billing, "companies_credits", credits)
    sign_in()

    response = client.get("/companies/credits")

    assert response.status_code == 200
    assert response.json() == [
        {"id": str(company.id), "name": "Acme", "available": 1_200, "low": False}
    ]
    # Only companies the user may top up: viewers spend no credits.
    assert asked == [EDITORS]


def test_a_taken_company_name_is_refused(client, monkeypatch):
    sign_in()

    async def none_owned(session, user_id):
        return 0

    async def name_taken(session, name, user_id, email, most=None):
        return None

    monkeypatch.setattr(companies, "owned_count", none_owned)
    monkeypatch.setattr(companies, "create", name_taken)

    response = client.post("/companies", json={"name": "Acme"}, headers={"Accept-Language": "de"})

    assert response.status_code == 409
    assert "Namen" in response.json()["detail"]


def test_an_unverified_email_creates_no_company(client, monkeypatch):
    """The welcome credits come once per email: a sign-in that didn't verify its address
    (GitHub's, say) can't claim someone else's."""
    sign_in(verified=False)
    made = []

    async def create(session, name, user_id, email, most=None):
        made.append(name)

    monkeypatch.setattr(companies, "create", create)

    response = client.post("/companies", json={"name": "Acme"})

    assert response.status_code == 403
    assert "Confirm your email" in response.json()["detail"]
    assert made == []


def test_a_company_name_longer_than_a_heading_is_refused(client):
    sign_in()

    response = client.post("/companies", json={"name": "x" * (MAX_COMPANY_NAME_LENGTH + 1)})

    assert response.status_code == 422


def test_a_company_without_its_welcome_credits_is_removed_again(client, monkeypatch):
    sign_in()
    created = Company(id=uuid.uuid4(), name="Acme", created_at=datetime.now(UTC))
    removed = []

    async def none_owned(session, user_id):
        return 0

    async def create(session, name, user_id, email, most=None):
        return created

    async def no_ids(session, user_id):
        return []

    async def billing_down(*args):
        raise RuntimeError("billing is down")

    async def remove(session, company_id):
        removed.append(company_id)

    monkeypatch.setattr(companies, "owned_count", none_owned)
    monkeypatch.setattr(companies, "create", create)
    monkeypatch.setattr(companies, "ids_for_user", no_ids)
    monkeypatch.setattr(billing, "welcome_company", billing_down)
    monkeypatch.setattr(companies, "delete", remove)

    with pytest.raises(RuntimeError):
        client.post("/companies", json={"name": "Acme"})

    # Trying again doesn't find the name taken.
    assert removed == [created.id]
