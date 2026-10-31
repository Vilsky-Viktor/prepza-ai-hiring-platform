import asyncio
import uuid

import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.key_actor import key_actor
from testee_common.auth.service_auth import issue_token

from companies.constants.ai_apps import KEY_OTHER_COMPANY
from companies.main import app
from companies.repositories import companies
from companies.repositories.audit import record as real_record
from companies.services.access import key_company, member_of
from tests.unit.api.v1.test_ai_apps import COMPANY_ID, SECRET, company  # noqa: F401 (fixture)

KEY_ID = uuid.uuid4()


def as_key(company_id=COMPANY_ID):
    """An AI agent signed in with a key of `company_id`, as the assistant calls: the key's own
    token, and the X-Assistant header naming its company and id."""
    claims = {"company": str(company_id), "key": str(KEY_ID)}
    token = issue_token("mcp", "companies", SECRET, claims)

    return {"Authorization": f"Bearer {token}", "X-Assistant": token}


@pytest.fixture
def signed_in_as_key(company):  # noqa: F811
    """No member signed in: the key acts as itself, and isn't one of Acme's members."""
    app.dependency_overrides.pop(current_user, None)

    return company


def test_a_key_reaches_its_own_company_as_itself_not_a_member(client, signed_in_as_key):
    response = client.get(f"/companies/{COMPANY_ID}", headers=as_key())

    assert response.status_code == 200
    assert response.json()["id"] == str(COMPANY_ID)
    assert key_actor(KEY_ID) not in [item.user_id for item in signed_in_as_key.members]


def test_without_its_header_a_key_is_no_member(client, signed_in_as_key):
    token = as_key()["Authorization"]
    response = client.get(f"/companies/{COMPANY_ID}", headers={"Authorization": token})

    assert response.status_code == 404


def test_a_key_is_refused_any_other_company(client, signed_in_as_key):
    other = uuid.uuid4()

    response = client.get(f"/companies/{other}", headers=as_key())

    assert response.status_code == 403
    assert response.json()["detail"] == KEY_OTHER_COMPANY


def test_a_key_lists_only_its_company_without_being_a_member(client, signed_in_as_key, monkeypatch):
    async def list_for_user(*args, **kwargs):
        raise AssertionError("a key is no member: its companies aren't looked up by membership")

    monkeypatch.setattr(companies, "list_for_user", list_for_user)

    listed = client.get("/companies", headers=as_key())
    later = client.get("/companies?offset=1", headers=as_key())

    assert [item["id"] for item in listed.json()] == [str(COMPANY_ID)]
    assert later.json() == []


def test_a_key_acts_as_an_admin_of_its_company_only_with_its_header(signed_in_as_key):
    from companies.core.security import REQUEST_COMPANY, REQUEST_KEY

    actor = key_actor(KEY_ID)

    assert member_of(signed_in_as_key, actor) is None
    assert key_company(actor) is None

    tokens = REQUEST_KEY.set(str(KEY_ID)), REQUEST_COMPANY.set(str(COMPANY_ID))

    try:
        acting = member_of(signed_in_as_key, actor)
        # Another key's id in the header makes this one nobody.
        REQUEST_KEY.set(str(uuid.uuid4()))
        other = member_of(signed_in_as_key, actor)
    finally:
        REQUEST_KEY.reset(tokens[0])
        REQUEST_COMPANY.reset(tokens[1])

    assert (acting.user_id, acting.role, acting.id) == (actor, "admin", None)
    assert other is None


def test_a_keys_action_is_audited_with_the_key(monkeypatch):
    added = []

    class FakeSession:
        def add(self, row):
            added.append(row)

    # The real one: the tests' audit log in memory replaces it.
    actor = key_actor(KEY_ID)
    asyncio.run(real_record(FakeSession(), COMPANY_ID, actor, "results_viewed", via="mcp"))
    asyncio.run(real_record(FakeSession(), COMPANY_ID, "bob", "results_viewed", via="mcp"))

    assert [(row.user_id, row.key_id, row.via) for row in added] == [
        (actor, KEY_ID, "mcp"),
        ("bob", None, "mcp"),
    ]
