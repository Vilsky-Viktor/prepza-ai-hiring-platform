import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from prepza_common.user import User

from app.constants.invites import COMPANY_SUSPENDED, INTERVIEW_UNAVAILABLE, InviteStatus
from app.models.companies import Company, Member
from app.routers import superadmin_companies as routes
from app.services import candidate_invites
from app.services.access import require_editor
from app.storage import companies, superadmin_companies
from tests.unit.test_invites import invite_page, stored_invite  # noqa: F401 (fixtures)

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

    async def search(q, limit):
        return [(suspended_company(), 2)]

    async def set_suspended(company_id, value):
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

    async def get(company_id):
        return suspended_company()

    async def rename(company_id, name):
        return name != "Taken"

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
    async def get(company_id):
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
    import app.routers.invites as invite_routes

    async def get(company_id):
        return suspended_company()

    monkeypatch.setattr(invite_routes.companies, "get", get)
    invite_page.status = current
    response = client.get("/invites/token-1")

    assert response.status_code == code

    if code == 410:
        assert response.json()["detail"] == INTERVIEW_UNAVAILABLE
