import pytest

from tests.unit.ats_route_fakes import connect as connect_ats
from tests.unit.ats_route_fakes import save_key, saved, stored_for


@pytest.fixture
def stored(monkeypatch, companies_api):
    return stored_for("recruitee", monkeypatch, companies_api)


def connect(client, account="acme.recruitee.com", token="good"):
    return connect_ats(client, "recruitee", account=account, token=token)


def test_recruitee_connects_with_the_companys_subdomain_and_token(client, stored):
    assert (
        connect(client, account=" https://Acme.recruitee.com/ ", token=" good ").status_code == 204
    )

    assert stored["checked"] == [("acme", "good")]
    assert saved(stored) == {"company": "acme", "token": "good"}
    assert stored["connection"].account == "acme"
    assert stored["connection"].member_id is None


def test_an_address_that_isnt_one_isnt_checked(client, stored):
    response = connect(client, account="not an address")

    assert response.status_code == 422
    assert response.json()["detail"] == "Enter your Recruitee address, like acme.recruitee.com"
    assert stored["checked"] == [] and stored["connection"] is None


@pytest.mark.parametrize("provider", ["workable", "greenhouse"])
def test_only_atss_that_make_the_secret_have_one_to_save(client, stored, provider):
    response = save_key(client, "web-hook-secret", provider)

    assert response.status_code == 404
    assert response.json()["detail"] == "No web hook key to save"
