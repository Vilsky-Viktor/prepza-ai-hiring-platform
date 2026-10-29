import pytest

from tests.unit.ats_route_fakes import connect as connect_ats
from tests.unit.ats_route_fakes import saved, stored_for, webhook


@pytest.fixture
def stored(monkeypatch, companies_api):
    return stored_for("greenhouse", monkeypatch, companies_api)


def connect(client, client_id="client-1234"):
    return connect_ats(client, "greenhouse", client_id=client_id)


def test_greenhouse_connects_with_a_secret_key_for_its_web_hook(client, stored):
    assert connect(client, client_id=" client-1234 ").status_code == 204

    found = saved(stored)
    # Greenhouse names no account: the page shows the company's name instead.
    assert stored["connection"].account == ""
    assert stored["connection"].member_id is None
    assert (found["client_id"], found["client_secret"]) == ("client-1234", "good")
    assert len(found["webhook_secret"]) >= 32

    found_webhook = webhook(client, "greenhouse").json()
    connection_id = stored["connection"].id
    assert found_webhook["url"].endswith(f"/api/ats/webhooks/greenhouse/{connection_id}")
    assert found_webhook["secret"] == found["webhook_secret"]


def test_a_reconnect_keeps_the_web_hooks_secret_key(client, stored):
    connect(client)
    first = saved(stored)["webhook_secret"]
    connect(client, client_id="client-5678")

    assert saved(stored)["webhook_secret"] == first
