import uuid

from prepza_common.auth.service_auth import issue_token

from api.repositories import keys, webhooks
from tests.unit.conftest import COMPANY

SECRET = "test-secret-that-is-at-least-32-bytes"
PATH = f"/internal/companies/{COMPANY}/active-count"


def headers(caller: str) -> dict:
    return {"Authorization": "Bearer " + issue_token(caller, "api", SECRET)}


def test_companies_reads_the_live_keys_and_working_web_hooks_of_the_company(client, monkeypatch):
    asked = []

    async def live_count(session, company_id, now):
        asked.append(("keys", company_id))

        return 2

    async def working_count(session, company_id):
        asked.append(("webhooks", company_id))

        return 1

    monkeypatch.setattr(keys, "live_count", live_count)
    monkeypatch.setattr(webhooks, "working_count", working_count)

    response = client.get(PATH, headers=headers("companies"))

    assert response.status_code == 200
    assert response.json() == {"count": 3}
    assert asked == [("keys", COMPANY), ("webhooks", COMPANY)]


def test_another_service_or_no_token_reads_no_count(client):
    assert client.get(PATH, headers=headers("assistant")).status_code == 403
    assert client.get(PATH).status_code == 401


def test_companies_reads_its_keys_names_as_they_are_now_and_no_one_else_may(client, monkeypatch):
    kept, gone = uuid.uuid4(), uuid.uuid4()
    asked = []

    async def names(session, company_id, key_ids):
        asked.append((company_id, sorted(key_ids)))

        return {kept: "Zapier"}

    monkeypatch.setattr(keys, "names", names)
    path = f"/internal/companies/{COMPANY}/keys/names"
    params = {"ids": [str(kept), str(gone)]}

    found = client.get(path, params=params, headers=headers("companies"))
    refused = client.get(path, params=params, headers=headers("assistant"))

    assert (found.status_code, found.json()) == (200, {str(kept): "Zapier"})
    assert asked == [(COMPANY, sorted([kept, gone]))]
    assert refused.status_code == 403
