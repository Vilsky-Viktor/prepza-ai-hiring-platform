"""The admin zone's support search, with the database, billing and accounts faked: one company,
Acme, with one interview and one candidate invite, and Ann's account."""

import asyncio
import uuid
from types import SimpleNamespace

import pytest

from companies.constants.superadmin import SUPPORT_RESULTS
from companies.integrations import accounts, billing
from companies.repositories import companies, superadmin_companies, superadmin_support
from companies.services import support_search

ACME = SimpleNamespace(id=uuid.uuid4(), name="Acme")
INTERVIEW = SimpleNamespace(id=uuid.uuid4(), title="Python developer", company_id=ACME.id)
INVITE = SimpleNamespace(id=uuid.uuid4(), email="cid@example.com", interview_id=INTERVIEW.id)
COMPANY = ("company", str(ACME.id), "Acme", ACME.id, "Acme")
INTERVIEW_RESULT = ("interview", str(INTERVIEW.id), "Python developer", ACME.id, "Acme")
CANDIDATE = ("candidate", str(INVITE.id), "cid@example.com", ACME.id, "Acme")
ANN = {"user_id": "uid-ann", "email": "ann@example.com", "created_at": None}
USER = ("user", "uid-ann", "ann@example.com", None, None)


@pytest.fixture(autouse=True)
def stored(monkeypatch):
    """The emails and names each search was asked for, in order."""
    asked = []

    async def get(session, company_id):
        return ACME if company_id == ACME.id else None

    async def interview(session, interview_id):
        return (INTERVIEW, ACME) if interview_id == INTERVIEW.id else None

    async def candidate(session, invite_id):
        return (INVITE, INTERVIEW, ACME) if invite_id == INVITE.id else None

    async def account(user_id):
        asked.append(("account", user_id))

        return ANN if user_id == ANN["user_id"] else None

    async def account_by_email(email):
        asked.append(("account", email))

        return ANN if email == ANN["email"] else None

    async def purchase_owner(transaction_id):
        return (
            {"owner_type": "company", "owner_id": str(ACME.id)}
            if transaction_id == "txn_01"
            else None
        )

    async def companies_of_member(session, email, limit):
        asked.append(("member", email))

        return [ACME] if email == "ann@example.com" else []

    async def invites_to(session, email, limit):
        asked.append(("candidate", email))

        return [(INVITE, ACME)] if email == "ann@example.com" else []

    async def companies_of_user(session, user_id, limit):
        asked.append(("user", user_id))

        return [(ACME, "owner")] if user_id == "uid-ann" else []

    async def search(session, q, limit):
        asked.append(("name", q, limit))

        return [(ACME, 2)] if q == "acm" else []

    monkeypatch.setattr(companies, "get", get)
    monkeypatch.setattr(superadmin_support, "interview", interview)
    monkeypatch.setattr(superadmin_support, "candidate", candidate)
    monkeypatch.setattr(accounts, "account", account)
    monkeypatch.setattr(accounts, "account_by_email", account_by_email)
    monkeypatch.setattr(billing, "purchase_owner", purchase_owner)
    monkeypatch.setattr(superadmin_support, "companies_of_member", companies_of_member)
    monkeypatch.setattr(superadmin_support, "invites_to", invites_to)
    monkeypatch.setattr(superadmin_support, "companies_of_user", companies_of_user)
    monkeypatch.setattr(superadmin_companies, "search", search)

    return asked


def found(query: str) -> list[tuple]:
    return [
        (row.kind, row.id, row.title, row.company_id, row.company_name)
        for row in asyncio.run(support_search.search(query))
    ]


def test_a_link_finds_the_deepest_page_it_points_at_on_any_host_and_language():
    company = f"https://prepza.com/de/companies/{ACME.id}"
    interview = f"{company}/interviews/{INTERVIEW.id}"

    assert found(company) == [COMPANY]
    assert found(f"{interview}?tab=settings") == [INTERVIEW_RESULT]
    candidate = f"http://localhost:3000/companies/{ACME.id}/interviews/{INTERVIEW.id}"

    assert found(f"{candidate}/candidates/{INVITE.id}") == [CANDIDATE]
    # A path alone does too.
    assert found(f"/companies/{ACME.id}/interviews/{INTERVIEW.id}") == [INTERVIEW_RESULT]


def test_an_id_finds_the_company_interview_or_candidate_that_has_it():
    assert found(str(ACME.id)) == [COMPANY]
    assert found(str(INTERVIEW.id)) == [INTERVIEW_RESULT]
    assert found(str(INVITE.id)) == [CANDIDATE]


def test_a_top_ups_transaction_finds_the_company_it_paid_into():
    assert found("txn_01") == [COMPANY]


def test_an_email_finds_its_account_its_members_companies_and_its_candidates(stored):
    assert found("ann@example.com") == [USER, COMPANY, CANDIDATE]
    assert stored == [
        ("account", "ann@example.com"),
        ("member", "ann@example.com"),
        ("candidate", "ann@example.com"),
    ]


def test_anything_else_finds_companies_by_name(stored):
    assert found("acm") == [COMPANY]
    assert stored == [("user", "acm"), ("name", "acm", SUPPORT_RESULTS), ("account", "acm")]


def test_an_account_id_finds_the_account_then_its_companies_once():
    """From "copy id" in the account menu or Settings; a company found both ways shows once."""
    assert found("uid-ann") == [USER, COMPANY]


def test_an_account_without_an_address_is_titled_by_its_id(monkeypatch):
    """A company's guest candidate."""

    async def account(user_id):
        return {"user_id": user_id, "email": None, "created_at": None}

    monkeypatch.setattr(accounts, "account", account)

    assert found("guest-1") == [("user", "guest-1", "guest-1", None, None)]


def test_unknown_ids_find_nothing():
    unknown = uuid.uuid4()

    assert found(str(unknown)) == []
    assert found(f"https://prepza.com/companies/{unknown}") == []
    assert found(f"/companies/{ACME.id}/interviews/{unknown}") == []
    assert found("txn_02") == []
    assert found("nobody@example.com") == []
    assert found("nothing like it") == []


def test_a_search_finds_at_most_the_limit(monkeypatch):
    async def many(session, email, limit):
        return [ACME] * limit

    monkeypatch.setattr(superadmin_support, "companies_of_member", many)

    assert len(found("ann@example.com")) == SUPPORT_RESULTS
