"""The Open to offers switch refuses what it can't record as a consent before saving anything
(the saves themselves: tests/integration/services/test_open_to_offers.py)."""

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from rounds.constants.open_to_offers import CONSENT_VERSION
from rounds.main import app
from rounds.services import open_to_offers


@pytest.fixture
def signed_in():
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True, name="Ann Lee"
    )


@pytest.fixture
def saved(monkeypatch):
    calls = []

    async def turn_on(user_id, name, linkedin_url, version, now):
        calls.append((user_id, name, linkedin_url, version))

        return open_to_offers.status_out(None)

    monkeypatch.setattr(open_to_offers, "turn_on", turn_on)

    return calls


@pytest.mark.parametrize(
    ("body", "status", "code", "detail"),
    [
        (
            {"linkedin_url": "https://www.linkedin.com/in/ann", "consent_version": "2020-01-01"},
            409,
            "consent_outdated",
            "The text you agreed to has changed. Reload the page and try again.",
        ),
        (
            {"linkedin_url": "https://example.com/ann", "consent_version": CONSENT_VERSION},
            422,
            "linkedin_invalid",
            "Enter your LinkedIn profile's address, like linkedin.com/in/your-name.",
        ),
    ],
)
def test_an_old_wording_or_an_address_that_isnt_a_profile_is_refused(
    client, signed_in, body, status, code, detail
):
    response = client.put("/open-to-offers", json=body)

    assert response.status_code == status
    assert (response.json()["code"], response.json()["detail"]) == (code, detail)


def test_turning_it_on_shares_the_sign_ins_name_and_the_profile(client, signed_in, saved):
    body = {"linkedin_url": "linkedin.com/in/ann", "consent_version": CONSENT_VERSION}

    assert client.put("/open-to-offers", json=body).status_code == 200
    assert saved == [("ann", "Ann Lee", "linkedin.com/in/ann", CONSENT_VERSION)]


def test_signed_out_people_cant_reach_the_switch(client):
    assert client.get("/open-to-offers").status_code == 401
