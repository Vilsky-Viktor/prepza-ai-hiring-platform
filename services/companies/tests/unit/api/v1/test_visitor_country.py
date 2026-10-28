"""The visitor's country (X-Client-Country) is optional where companies reads it (creating a
company): calls from the assistant, AI apps, the public API and other services have none, and
billing then goes by the saved currency (or US dollars). With it, it's passed on to billing as it
came. Billing's own company routes read it themselves (its tests)."""

import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.integrations import billing
from companies.main import app
from companies.models.companies import Company
from companies.repositories import companies

HEADER = "X-Client-Country"


@pytest.mark.parametrize("country", [None, "GB"])
def test_a_company_is_created_without_the_country_and_billing_gets_it_with_one(
    client, monkeypatch, country
):
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    created = Company(id=uuid.uuid4(), name="Acme", created_at=datetime.now(UTC))
    welcomed = []

    async def none_owned(session, user_id):
        return 0

    async def create(session, name, user_id, email, most=None):
        return created

    async def no_ids(session, user_id):
        return []

    async def welcome(company_id, email, referral, related, from_country):
        welcomed.append(from_country)

    monkeypatch.setattr(companies, "owned_count", none_owned)
    monkeypatch.setattr(companies, "create", create)
    monkeypatch.setattr(companies, "ids_for_user", no_ids)
    monkeypatch.setattr(billing, "welcome_company", welcome)
    headers = {HEADER: country} if country else {}

    client.post("/companies", json={"name": "Acme"}, headers=headers)
    app.dependency_overrides.clear()

    assert welcomed == [country]
