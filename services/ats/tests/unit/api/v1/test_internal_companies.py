import uuid

from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from ats.repositories import ats

SECRET = "test-secret-that-is-at-least-32-bytes"
COMPANY = uuid.uuid4()
PATH = f"/internal/companies/{COMPANY}/active-count"


def headers(caller: str) -> dict:
    return bearer(issue_token(caller, "ats", SECRET))


def test_companies_reads_how_many_of_the_companys_atss_work(client, monkeypatch):
    asked = []

    async def connected_count(session, company_id):
        asked.append(company_id)

        return 2

    monkeypatch.setattr(ats, "connected_count", connected_count)

    response = client.get(PATH, headers=headers("companies"))

    assert response.json() == {"count": 2}
    assert asked == [COMPANY]


def test_another_service_or_no_token_reads_no_count(client):
    assert client.get(PATH, headers=headers("assistant")).status_code == 403
    assert client.get(PATH).status_code == 401
