import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from testee_common.auth.user import User

from companies.constants.invites import COMPANY_SUSPENDED, INTERVIEW_UNAVAILABLE, InviteStatus
from companies.models.companies import Company, Member
from companies.repositories import companies, superadmin_companies
from companies.services import candidate_invites
from companies.services import superadmin_companies as routes
from companies.services.access import require_editor
from tests.unit.api.v1.test_invites import invite_page, stored_invite  # noqa: F401 (fixtures)

COMPANY_ID = uuid.uuid4()


def suspended_company() -> Company:
    company = Company(
        id=COMPANY_ID,
        name="Google",
        suspended_at=datetime.now(UTC),
        verification_status="none",
        created_at=datetime.now(UTC),
    )
    company.members = [Member(company_id=COMPANY_ID, user_id="ann", role="owner")]

    return company


def test_only_a_superadmin_finds_and_suspends_companies(client, superadmin, monkeypatch):
    suspended = []

    async def search(session, q, limit):
        return [(suspended_company(), 2)]

    async def set_suspended(session, company_id, value):
        suspended.append(value)

        return True

    monkeypatch.setattr(superadmin_companies, "search", search)
    monkeypatch.setattr(superadmin_companies, "set_suspended", set_suspended)
    url = f"/superadmin/companies/{COMPANY_ID}"

    superadmin("bob@example.com")
    assert client.get("/superadmin/companies").status_code == 404
    assert client.post(f"{url}/suspend").status_code == 404

    superadmin("ann@example.com")
    [found] = client.get("/superadmin/companies", params={"q": "goo"}).json()
    assert (found["name"], found["members"], found["suspended"]) == ("Google", 2, True)
    assert client.post(f"{url}/suspend").status_code == 204
    assert client.post(f"{url}/unsuspend").status_code == 204
    assert suspended == [True, False]


def test_a_superadmin_renames_to_a_free_name_and_deletes(client, superadmin, monkeypatch):
    deleted = []

    async def get(session, company_id):
        return suspended_company()

    async def rename(session, company_id, name):
        if name == "Taken":
            raise IntegrityError("UPDATE", {}, Exception(companies.NAME_INDEX))

    async def delete_company(company_id):
        deleted.append(company_id)

    monkeypatch.setattr(companies, "get", get)
    monkeypatch.setattr(companies, "rename", rename)
    monkeypatch.setattr(routes.company_deletion, "delete_company", delete_company)
    superadmin("ann@example.com")
    url = f"/superadmin/companies/{COMPANY_ID}"

    assert client.put(f"{url}/name", json={"name": "Not Google"}).status_code == 204
    assert client.put(f"{url}/name", json={"name": "Taken"}).status_code == 409
    assert client.delete(url).status_code == 204
    assert deleted == [COMPANY_ID]


def test_a_suspended_company_is_read_not_changed(monkeypatch):
    async def get(session, company_id):
        return suspended_company()

    monkeypatch.setattr(companies, "get", get)
    owner = User(
        uid="ann", email="ann@example.com", email_verified=True, sign_in_provider="google.com"
    )

    with pytest.raises(HTTPException) as refused:
        asyncio.run(require_editor(owner, COMPANY_ID))

    assert (refused.value.status_code, refused.value.detail) == (403, COMPANY_SUSPENDED)


def test_a_suspended_company_invites_nobody(monkeypatch):
    """409: an ATS keeps its candidates waiting, to invite once it's lifted."""
    interview = SimpleNamespace(id=uuid.uuid4())

    with pytest.raises(HTTPException) as refused:
        asyncio.run(candidate_invites.invite(interview, suspended_company(), None, "x@y.com"))

    assert refused.value.status_code == 409


@pytest.mark.parametrize(("current", "code"), [(InviteStatus.INVITED, 410), ("in_process", 200)])
def test_candidates_find_its_interview_unavailable_unless_already_in_it(
    client,
    invite_page,  # noqa: F811
    monkeypatch,
    current,
    code,
):
    async def get(session, company_id):
        return suspended_company()

    monkeypatch.setattr(companies, "get", get)
    invite_page.status = current
    response = client.get("/invites/token-1")

    assert response.status_code == code

    if code == 410:
        assert response.json()["detail"] == INTERVIEW_UNAVAILABLE
