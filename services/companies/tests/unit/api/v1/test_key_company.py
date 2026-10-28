import asyncio
import uuid

from prepza_common.auth.service_auth import issue_token

from companies.constants.ai_apps import KEY_OTHER_COMPANY
from companies.repositories import audit, companies
from companies.repositories.audit import record as real_record
from tests.unit.api.v1.test_ai_apps import COMPANY_ID, SECRET, company  # noqa: F401 (fixture)

KEY_ID = uuid.uuid4()


def as_key(company_id=COMPANY_ID):
    """The X-Assistant header of an AI agent signed in with a key of `company_id`."""
    claims = {"company": str(company_id), "key": str(KEY_ID)}

    return {"X-Assistant": issue_token("mcp", "companies", SECRET, claims)}


def test_a_key_reaches_its_own_company(client, company):  # noqa: F811
    response = client.get(f"/companies/{COMPANY_ID}", headers=as_key())

    assert response.status_code == 200
    assert response.json()["id"] == str(COMPANY_ID)


def test_a_key_is_refused_any_other_company(client, company):  # noqa: F811
    other = uuid.uuid4()

    response = client.get(f"/companies/{other}", headers=as_key())

    assert response.status_code == 403
    assert response.json()["detail"] == KEY_OTHER_COMPANY


def test_a_key_lists_only_its_company(client, company, monkeypatch):  # noqa: F811
    acme = company
    asked = []

    async def list_for_user(session, user_id, offset, limit, roles=None, only=None):
        asked.append(only)

        return [acme]

    monkeypatch.setattr(companies, "list_for_user", list_for_user)

    client.get("/companies", headers=as_key())
    client.get("/companies")

    assert asked == [str(COMPANY_ID), None]


def test_a_keys_action_is_audited_with_the_key(monkeypatch):
    added = []

    class FakeSession:
        def add(self, row):
            added.append(row)

    token = audit.REQUEST_KEY.set(str(KEY_ID))

    # The real one: the tests' audit log in memory replaces it.
    try:
        asyncio.run(real_record(FakeSession(), COMPANY_ID, "bob", "results_viewed", via="mcp"))
    finally:
        audit.REQUEST_KEY.reset(token)

    assert added[0].key_id == KEY_ID
    assert added[0].via == "mcp"
