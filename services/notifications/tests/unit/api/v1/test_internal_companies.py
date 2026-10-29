import uuid

import pytest
from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from notifications.repositories import slack

SECRET = "test-secret-that-is-at-least-32-bytes"
COMPANY = uuid.uuid4()
PATH = f"/internal/companies/{COMPANY}/active-count"


def headers(caller: str) -> dict:
    return bearer(issue_token(caller, "notifications", SECRET))


@pytest.mark.parametrize(("channel", "count"), [(object(), 1), (None, 0)])
def test_companies_reads_whether_the_companys_slack_works(client, monkeypatch, channel, count):
    asked = []

    async def connected(session, company_id):
        asked.append(company_id)

        return channel

    monkeypatch.setattr(slack, "connected", connected)

    response = client.get(PATH, headers=headers("companies"))

    assert response.json() == {"count": count}
    assert asked == [str(COMPANY)]


def test_another_service_or_no_token_reads_no_count(client):
    assert client.get(PATH, headers=headers("assistant")).status_code == 403
    assert client.get(PATH).status_code == 401
