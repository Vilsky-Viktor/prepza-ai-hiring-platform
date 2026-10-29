"""What the key-based ATSs' routes do alike, one case per ATS; each ATS's own steps are in its
test_ats_<provider>_routes.py."""

import hashlib
import hmac
import uuid

import pytest

from ats.constants.ats import GREENHOUSE_CANT_WRITE
from tests.unit.ats_route_fakes import connect, save_key, saved, stored_for, webhook
from tests.unit.helpers.test_teamtailor_signatures import signature as teamtailor_signature
from tests.unit.integrations.test_breezy import signature as breezy_signature
from tests.unit.integrations.test_recruitee import signature as recruitee_signature

# The ATSs whose web hook secret the company copies from the ATS and saves in prepza.
SAVED_SECRET = ["recruitee", "teamtailor"]


def greenhouse_signature(secret: str, body: bytes) -> str:
    return "sha256 " + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.mark.parametrize(
    ("provider", "body", "rows", "detail"),
    [
        ("breezy", {"token": "bad"}, {}, "Breezy HR didn't accept this key"),
        ("breezy", {"token": "nobody"}, {}, "This key's person has no Breezy HR company"),
        (
            "greenhouse",
            {"client_secret": "bad"},
            {},
            "Greenhouse didn't accept this client ID and secret",
        ),
        # Results couldn't go back: Greenhouse lists its scopes without the one notes need.
        ("greenhouse", {}, {"can_write": False}, GREENHOUSE_CANT_WRITE),
        (
            "recruitee",
            {"token": "bad"},
            {},
            "Recruitee didn't accept this token for that company",
        ),
        (
            "teamtailor",
            {"key": "bad"},
            {},
            "Teamtailor didn't accept this key: it needs Admin and Read/Write",
        ),
    ],
)
def test_a_refused_credential_isnt_saved(
    client, monkeypatch, companies_api, provider, body, rows, detail
):
    stored = stored_for(provider, monkeypatch, companies_api)
    stored.update(rows)
    response = connect(client, provider, **body)

    assert response.status_code == 422
    assert response.json()["detail"] == detail
    assert stored["connection"] is None
    assert stored.get("hooks", []) == []
    assert webhook(client, provider).status_code == 404


@pytest.mark.parametrize("provider", SAVED_SECRET)
def test_saving_a_secret_needs_a_connection(client, monkeypatch, companies_api, provider):
    stored_for(provider, monkeypatch, companies_api)

    assert save_key(client, "web-hook-secret", provider).status_code == 404


@pytest.mark.parametrize("provider", SAVED_SECRET)
def test_the_web_hook_has_no_secret_until_one_is_saved_and_a_reconnect_keeps_it(
    client, monkeypatch, companies_api, provider
):
    stored = stored_for(provider, monkeypatch, companies_api)
    connect(client, provider)
    connection_id = stored["connection"].id
    credentials = saved(stored)
    before = webhook(client, provider).json()

    assert before["url"].endswith(f"/api/ats/webhooks/{provider}/{connection_id}")
    assert before["secret"] == ""

    assert save_key(client, " web-hook-secret ", provider).status_code == 204
    assert saved(stored) == {**credentials, "webhook_secret": "web-hook-secret"}
    assert webhook(client, provider).json()["secret"] == "web-hook-secret"

    connect(client, provider)

    assert saved(stored)["webhook_secret"] == "web-hook-secret"
    assert stored["connection"].id == connection_id


@pytest.mark.parametrize(
    ("provider", "header", "sign", "body", "unsaved"),
    [
        # Breezy and Greenhouse have their secret from the connect itself.
        (
            "breezy",
            "X-Hook-Signature",
            breezy_signature,
            b'{"type": "candidateStatusUpdated", "object": {}}',
            None,
        ),
        ("greenhouse", "Signature", greenhouse_signature, b'{"action": "ping"}', None),
        # Before the secret is saved, Recruitee's events (its test among them) are answered
        # and ignored; nothing counts for Teamtailor.
        (
            "recruitee",
            "X-Recruitee-Signature",
            recruitee_signature,
            b'{"event_type": "candidate_moved", "event_subtype": "stage_changed", "payload": {}}',
            200,
        ),
        (
            "teamtailor",
            "TT-Signature",
            teamtailor_signature,
            b'{"event_name": "candidate.update", "data": {"id": 1}}',
            401,
        ),
    ],
)
def test_the_web_hook_answers_only_what_its_secret_signed(
    client, monkeypatch, companies_api, provider, header, sign, body, unsaved
):
    stored = stored_for(provider, monkeypatch, companies_api)
    connect(client, provider)
    url = f"/webhooks/{provider}/{stored['connection'].id}"

    if unsaved is not None:
        assert client.post(url, content=body).status_code == unsaved

        save_key(client, "web-hook-secret", provider)

    secret = saved(stored)["webhook_secret"]
    signed = {header: sign(secret, body)}
    forged = {header: sign("other", body)}

    assert client.post(url, content=body, headers=signed).status_code == 200
    assert client.post(url, content=body, headers=forged).status_code == 401
    assert client.post(url, content=body).status_code == 401
    # An address no connection has is answered, so the ATS doesn't keep sending.
    assert client.post(f"/webhooks/{provider}/{uuid.uuid4()}", content=body).status_code == 200
