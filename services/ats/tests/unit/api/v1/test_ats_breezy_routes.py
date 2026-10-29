import pytest
from fastapi import HTTPException

from ats.integrations import breezy
from ats.integrations.errors import KeyRejected
from tests.unit.ats_route_fakes import COMPANY_ID, saved, stored_for
from tests.unit.ats_route_fakes import connect as connect_ats


@pytest.fixture
def stored(monkeypatch, companies_api):
    return stored_for("breezy", monkeypatch, companies_api)


def connect(client, token="good"):
    return connect_ats(client, "breezy", token=token)


def test_breezy_connects_with_a_key_and_creates_its_web_hook(client, stored):
    assert connect(client, token=" good ").status_code == 204

    connection_id = stored["connection"].id
    assert stored["connection"].account == "Acme"
    assert stored["connection"].member_id is None
    assert stored["hooks"][0].endswith(f"/api/ats/webhooks/breezy/{connection_id}")
    assert saved(stored) == {
        "company": "c1",
        "token": "good",
        "webhook_id": "w1",
        "webhook_secret": "secret-1",
    }


@pytest.mark.parametrize("failure", [KeyRejected(), HTTPException(502)])
def test_without_its_web_hook_the_connection_doesnt_stay(client, stored, monkeypatch, failure):
    async def refuse(company, token, url):
        raise failure

    monkeypatch.setattr(breezy, "subscribe", refuse)
    response = connect(client)

    assert response.status_code == 409
    assert "web hooks come with Breezy's Pro plan" in response.json()["detail"]
    assert stored["connection"] is None
    # Disconnected as Ann's, so the company's action log shows it didn't stay.
    assert stored["disconnected_by"] == ["ann"]


def test_a_failed_reconnect_keeps_the_earlier_connection_marked_for_reconnecting(
    client, stored, monkeypatch
):
    connect(client)
    earlier = stored["connection"]

    async def refuse(company, token, url):
        raise HTTPException(502)

    monkeypatch.setattr(breezy, "subscribe", refuse)
    response = connect(client)

    assert response.status_code == 409
    # Not disconnected (which would delete its linked jobs and candidates): its key is back.
    assert stored["connection"].id == earlier.id
    assert stored["connection"].status == "broken"
    assert saved(stored)["webhook_secret"] == "secret-1"


def test_a_reconnect_replaces_the_earlier_web_hook(client, stored):
    connect(client)
    connection_id = stored["connection"].id
    connect(client)

    assert stored["deleted"] == ["w1"]
    assert saved(stored)["webhook_id"] == "w2"
    assert stored["connection"].id == connection_id


def test_disconnecting_deletes_the_web_hook(client, stored):
    connect(client)

    assert client.delete(f"/breezy?company_id={COMPANY_ID}").status_code == 204
    assert stored["deleted"] == ["w1"]
    assert stored["connection"] is None
    assert stored["disconnected_by"] == ["ann"]
