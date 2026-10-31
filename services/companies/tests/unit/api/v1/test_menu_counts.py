"""The company's menu counts: its interviews and team from its own rows, its working integrations
from ats, notifications, the api service and the assistant, its referral rewards from billing. A
service that fails adds nothing; when none answers, or billing doesn't, that part is None."""

import uuid
from datetime import UTC, datetime

import httpx
import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.http import http

from companies.integrations import billing
from companies.main import app
from companies.models.companies import Company, Member
from companies.repositories import companies, interviews

COMPANY_ID = uuid.uuid4()
COUNTS = {"ats": 2, "notifications": 1, "api": 3, "assistant": 1}


def member(user_id: str | None, email: str, role: str) -> Member:
    return Member(
        company_id=COMPANY_ID,
        user_id=user_id,
        invited_email=email,
        role=role,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def company(monkeypatch):
    """Acme: an owner, a viewer, a pending invite and 4 interviews; bob (the viewer) signed in."""
    found = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    found.members = [
        member("ann", "ann@example.com", "owner"),
        member("bob", "bob@example.com", "viewer"),
        member(None, "cid@example.com", "admin"),
    ]

    async def get_company(session, company_id):
        return found if company_id == COMPANY_ID else None

    async def counts(session, company_ids):
        return {COMPANY_ID: 4}

    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(interviews, "counts", counts)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )
    yield found
    app.dependency_overrides.clear()


@pytest.fixture
def services(monkeypatch):
    """Each service's count, by host; a host listed in `down` answers 503. Returns the paths
    called and `down`."""
    called, down = [], set()

    def handler(request):
        called.append(request.url.path)

        if request.url.host in down:
            return httpx.Response(503)

        return httpx.Response(200, json={"count": COUNTS[request.url.host]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(http, "get_client", lambda: client)

    async def referral(company_id):
        return {"rewarded": 2}

    monkeypatch.setattr(billing, "company_referral", referral)

    return called, down


def test_each_count_comes_from_its_place(client, company, services):
    called, _ = services
    response = client.get(f"/companies/{COMPANY_ID}/menu-counts")

    assert response.json() == {"interviews": 4, "members": 3, "integrations": 7, "referrals": 2}
    # The AI apps are the signed-in member's own.
    assert sorted(called) == sorted(
        [f"/internal/companies/{COMPANY_ID}/active-count"] * 3
        + ["/internal/users/bob/active-count"]
    )


@pytest.mark.parametrize(
    ("down", "integrations"),
    [({"ats"}, 5), ({"assistant", "api"}, 3), ({"ats", "notifications", "api", "assistant"}, None)],
)
def test_a_service_that_fails_adds_nothing(client, company, services, down, integrations):
    services[1].update(down)

    found = client.get(f"/companies/{COMPANY_ID}/menu-counts").json()

    assert (found["interviews"], found["integrations"]) == (4, integrations)


def test_ai_apps_count_only_while_the_company_allows_them(client, company, services):
    company.ai_apps_off_at = datetime.now(UTC)

    found = client.get(f"/companies/{COMPANY_ID}/menu-counts").json()

    assert found["integrations"] == 6
    assert "/internal/users/bob/active-count" not in services[0]


@pytest.mark.parametrize("error", [httpx.ConnectError("down"), TimeoutError()])
def test_no_referral_count_without_billing(client, company, services, monkeypatch, error):
    async def failing(company_id):
        raise error

    monkeypatch.setattr(billing, "company_referral", failing)

    found = client.get(f"/companies/{COMPANY_ID}/menu-counts").json()

    assert (found["referrals"], found["integrations"]) == (None, 7)


def test_only_a_member_sees_the_counts(client, company, services):
    app.dependency_overrides[current_user] = lambda: User(
        uid="dan", email="dan@example.com", email_verified=True
    )

    response = client.get(f"/companies/{COMPANY_ID}/menu-counts")

    assert response.status_code == 404
    assert services[0] == []
