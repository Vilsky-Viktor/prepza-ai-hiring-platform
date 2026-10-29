import socket

import pytest
from prepza_common.auth.encryption import decrypt
from prepza_common.auth.tokens import hashed
from prepza_common.http import public_urls

from api.services import manage
from tests.unit.conftest import COMPANY, KEY, sign_in

KEYS = f"/manage/keys?company_id={COMPANY}"
HOOKS = f"/manage/webhooks?company_id={COMPANY}"


def test_a_new_key_is_shown_once_and_stored_as_its_hash(client, companies_api, stored):
    sign_in()
    made = client.post(KEYS, json={"name": " Careers site ", "expiry": "3"}).json()
    listed = client.get(f"/manage?company_id={COMPANY}").json()

    assert made["key"].startswith("pz_")
    assert stored["keys"][0].hash == hashed(made["key"])
    assert stored["keys"][0].name == "Careers site"
    assert stored["keys"][0].created_by == "u1"
    assert "key" not in listed["keys"][0]
    assert listed["expiries"] == ["1", "3", "6", "12", "never"]


@pytest.mark.parametrize(("expiry", "months"), [("1", 1), ("12", 12), ("never", None)])
def test_a_key_expires_as_chosen(client, companies_api, stored, expiry, months):
    sign_in()
    made = client.post(KEYS, json={"name": "Site", "expiry": expiry}).json()
    created = stored["keys"][0]

    if months is None:
        assert made["expires_at"] is None
    else:
        assert created.expires_at.month == (created.created_at.month - 1 + months) % 12 + 1
    assert made["expired"] is False


@pytest.mark.parametrize("body", [{"name": "Site"}, {"name": "Site", "expiry": "2"}, {"name": ""}])
def test_a_key_needs_a_name_and_a_known_expiry(client, companies_api, stored, body):
    sign_in()

    assert client.post(KEYS, json=body).status_code == 422
    assert stored["keys"] == []


def test_a_viewer_sees_but_cant_change_and_a_stranger_sees_nothing(client, companies_api, stored):
    companies_api["roles"] = {"u1": "viewer"}
    sign_in()

    assert client.get(f"/manage?company_id={COMPANY}").status_code == 200
    assert client.post(KEYS, json={"name": "Site", "expiry": "1"}).status_code == 403
    assert client.post(HOOKS, json={"url": "https://example.com/x"}).status_code == 403

    sign_in("stranger")

    assert client.get(f"/manage?company_id={COMPANY}").status_code == 404


@pytest.fixture
def public(monkeypatch):
    """Every address counts as on the public internet unless it has "internal" in it; one with
    "unknown" in it doesn't resolve."""

    def check(url):
        if "unknown" in url:
            raise socket.gaierror

        return None if "internal" in url else "203.0.113.10"

    monkeypatch.setattr(public_urls, "public_address", check)


def test_a_web_hook_gets_a_secret_shown_once_and_stored_encrypted(
    client, companies_api, stored, public
):
    sign_in()
    made = client.post(HOOKS, json={"url": " https://example.com/x "}).json()
    sealed = stored["webhooks"][0].secret

    assert made["secret"].startswith("whsec_")
    assert stored["webhooks"][0].url == "https://example.com/x"
    assert made["secret"] not in sealed
    assert decrypt(KEY, sealed) == made["secret"]


def test_the_api_page_shows_which_web_hooks_are_failing(client, companies_api, stored, public):
    sign_in()
    client.post(HOOKS, json={"url": "https://ok.example/x"})
    client.post(HOOKS, json={"url": "https://down.example/x"})
    stored["webhooks"][1].failing = True
    shown = client.get(f"/manage?company_id={COMPANY}").json()["webhooks"]

    assert [(hook["url"], hook["failing"]) for hook in shown] == [
        ("https://ok.example/x", False),
        ("https://down.example/x", True),
    ]


def test_a_web_hook_added_by_someone_no_longer_an_editor_shows_as_working(
    client, companies_api, stored, public
):
    sign_in()
    client.post(HOOKS, json={"url": "https://left.example/x"})
    stored["webhooks"][0].created_by = "u2"
    companies_api["roles"]["u2"] = "viewer"
    [shown] = client.get(f"/manage?company_id={COMPANY}").json()["webhooks"]

    assert (shown["url"], shown["failing"]) == ("https://left.example/x", False)
    assert "stopped" not in shown


def test_only_owners_and_admins_see_a_web_hooks_whole_address(
    client, companies_api, stored, public
):
    """A Zapier or Make address works like a password: a viewer sees its site only."""
    sign_in()
    client.post(HOOKS, json={"url": "https://hooks.zapier.com/hooks/catch/123/abc"})
    [owner] = client.get(f"/manage?company_id={COMPANY}").json()["webhooks"]
    companies_api["roles"]["u2"] = "viewer"
    sign_in("u2")
    [viewer] = client.get(f"/manage?company_id={COMPANY}").json()["webhooks"]

    assert owner["url"] == "https://hooks.zapier.com/hooks/catch/123/abc"
    assert viewer["url"] == "https://hooks.zapier.com/…"


def test_a_web_hook_must_reach_the_public_internet(client, companies_api, stored, public):
    sign_in()
    response = client.post(HOOKS, json={"url": "https://internal/x"})

    assert response.status_code == 422
    assert client.post(HOOKS, json={"url": "https://unknown/x"}).status_code == 422
    assert stored["webhooks"] == []


def test_without_an_encryption_key_web_hooks_cant_be_added(
    client, companies_api, stored, monkeypatch
):
    monkeypatch.setattr(manage.settings, "api_encryption_key", "")
    sign_in()
    response = client.post(HOOKS, json={"url": "https://example.com/x"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Web hooks aren't set up yet"


def test_deleting_what_isnt_there_is_not_found(client, companies_api, monkeypatch):
    async def nothing(session, company_id, item_id, user_id):
        return False

    monkeypatch.setattr(manage.keys, "remove", nothing)
    monkeypatch.setattr(manage.webhooks, "remove", nothing)
    sign_in()

    assert client.delete(f"/manage/keys/{COMPANY}?company_id={COMPANY}").status_code == 404
    assert client.delete(f"/manage/webhooks/{COMPANY}?company_id={COMPANY}").status_code == 404
