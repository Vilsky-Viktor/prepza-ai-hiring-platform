"""The visitor's country (X-Client-Country) is optional on every route that reads it: calls from
the assistant, AI apps, the public API and other services have none, and billing then goes by
the saved currency (or US dollars). With it, it's passed on to billing as it came."""

import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.api.v1 import billing as billing_routes
from companies.integrations import billing, billing_prices
from companies.main import app
from companies.models.companies import Company, Member
from companies.repositories import audit, companies

COMPANY_ID = uuid.uuid4()
COMPANY = f"/companies/{COMPANY_ID}"
HEADER = "X-Client-Country"
AUTO_TOP_UP = {
    "offered": True,
    "on": False,
    "waiting": False,
    "product": None,
    "threshold": None,
    "products": ["topup_50"],
    "thresholds": [500],
    "currency": "USD",
    "prices": {"topup_50": 5000},
}
CURRENCY = {"currency": "USD", "currencies": ["USD", "EUR", "GBP"]}


@pytest.fixture
def passed(monkeypatch):
    """Bob, an admin of the company, signed in; the country each billing call was given."""
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role="admin",
            created_at=datetime.now(UTC),
        )
    ]
    countries = []

    async def get(_company_id):
        return company

    def answering(answer):
        async def call(*args, **kwargs):
            countries.append(args[-1])

            return answer

        return call

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(companies, "get", get)
    monkeypatch.setattr(billing_prices, "auto_top_up", answering(AUTO_TOP_UP))
    monkeypatch.setattr(billing_prices, "catalog", answering({"currency": "USD"}))
    monkeypatch.setattr(billing_prices, "currency", answering(CURRENCY))
    monkeypatch.setattr(billing_prices, "company_checkout", answering("txn_01"))
    monkeypatch.setattr(billing_routes, "count_checkout_call", nothing)
    monkeypatch.setattr(audit, "record", nothing)

    yield countries

    app.dependency_overrides.clear()


@pytest.mark.parametrize("country", [None, "DE"])
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/auto-top-up", None),
        ("GET", "/billing/catalog", None),
        ("GET", "/billing/currency", None),
        ("POST", "/billing/checkout", {"candidates": 10}),
    ],
)
def test_a_route_works_without_the_country_and_passes_it_on_with_one(
    client, passed, method, path, body, country
):
    headers = {HEADER: country} if country else {}

    response = client.request(method, f"{COMPANY}{path}", json=body, headers=headers)

    assert response.status_code == 200
    assert passed == [country]


@pytest.mark.parametrize("country", [None, "GB"])
def test_a_company_is_created_without_the_country_and_billing_gets_it_with_one(
    client, monkeypatch, country
):
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    created = Company(id=uuid.uuid4(), name="Acme", created_at=datetime.now(UTC))
    welcomed = []

    async def none_owned(user_id):
        return 0

    async def create(name, user_id, email, most=None):
        return created

    async def no_ids(user_id):
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


def test_a_pages_server_passes_the_visitors_country_over_its_own(client, passed):
    # A page's server calls through the load balancer, which sets its own country in the header.
    response = client.get(f"{COMPANY}/billing/currency?country=DE", headers={HEADER: "US"})

    assert response.status_code == 200
    assert passed == ["DE"]
