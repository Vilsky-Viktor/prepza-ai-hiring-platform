import pytest
from cryptography.fernet import Fernet

from tests.unit.ats_route_fakes import TEAMTAILOR_HOST as HOST
from tests.unit.ats_route_fakes import connect as connect_ats
from tests.unit.ats_route_fakes import save_key, saved, stored_for, webhook


@pytest.fixture
def stored(monkeypatch, companies_api):
    return stored_for("teamtailor", monkeypatch, companies_api)


def connect(client, key="good"):
    return connect_ats(client, "teamtailor", key=key)


def test_teamtailor_connects_with_its_region_company_name_and_member(client, stored):
    assert connect(client, key=" good ").status_code == 204

    assert saved(stored) == {"host": HOST, "key": "good"}
    assert stored["connection"].account == "Acme"
    assert stored["connection"].member_id == "5"
    assert stored["members"] == ["ann@example.com"]


def test_only_greenhouse_and_teamtailor_have_a_web_hook_to_set_up(client, stored):
    response = webhook(client, "workable")

    assert response.status_code == 404
    assert response.json()["detail"] == "No web hook to set up"
    # Greenhouse's, while it isn't connected.
    assert webhook(client, "greenhouse").json()["detail"] == "Not connected"


def test_a_reconnect_after_the_encryption_key_changed_works_without_the_old_signature_key(
    client, stored
):
    connect(client)
    save_key(client, "signature-key", "teamtailor")
    # Sealed with an encryption key that's gone.
    stored["connection"].credentials = Fernet(Fernet.generate_key()).encrypt(b"{}").decode()

    assert connect(client).status_code == 204
    assert saved(stored) == {"host": HOST, "key": "good"}
