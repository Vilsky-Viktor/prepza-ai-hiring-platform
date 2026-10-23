"""The interviews list's search: the route hands storage the title search, trimmed, and refuses
one too long."""

import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.main import app
from app.models.companies import Company, Member
from app.storage import candidates, companies, interviews

COMPANY_ID = uuid.uuid4()
URL = "/interviews"


@pytest.fixture
def asked(monkeypatch):
    """bob, a viewer of the company, signed in; the searches storage was asked for."""
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="viewer")
    ]
    searches = []

    async def found(_company_id):
        return company

    async def listed(company_id, offset, limit, q=""):
        searches.append((company_id, offset, limit, q))

        return []

    async def counts(_ids):
        return {}

    monkeypatch.setattr(companies, "get", found)
    monkeypatch.setattr(interviews, "list_for_company", listed)
    monkeypatch.setattr(candidates, "counts", counts)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )
    yield searches
    app.dependency_overrides.clear()


def test_a_search_is_trimmed_and_kept_across_pages(client, asked):
    params = {"company_id": str(COMPANY_ID), "q": " SQL_b ", "offset": 20, "limit": 10}
    response = client.get(URL, params=params)

    assert response.status_code == 200
    assert asked == [(COMPANY_ID, 20, 10, "SQL_b")]


def test_no_search_lists_every_interview(client, asked):
    client.get(URL, params={"company_id": str(COMPANY_ID)})

    assert asked[0][3] == ""


def test_a_search_longer_than_the_limit_is_refused(client, asked):
    response = client.get(URL, params={"company_id": str(COMPANY_ID), "q": "a" * 255})

    assert response.status_code == 422
    assert asked == []
