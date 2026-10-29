# The fixtures and the company are the internal ATS routes' tests'.
# ruff: noqa: F811
import pytest

from companies.constants.return_urls import RETURN_URL_INVALID
from tests.unit.api.v1.test_internal_ats import (  # noqa: F401 (fixture)
    COMPANY,
    HEADERS,
    READY,
    stored,
)


@pytest.mark.parametrize(
    "return_url", ["https://elsewhere.com/next?step=2", "http://localhost:3000/done"]
)
def test_a_return_address_on_any_https_host_or_localhost_invites(
    client, stored, monkeypatch, return_url
):
    # Nothing to do with the allowed domains, which are only for embedding.
    monkeypatch.setattr(COMPANY, "allowed_domains", [], raising=False)
    monkeypatch.setattr(COMPANY, "allow_localhost", False, raising=False)
    body = {"email": "cara@example.com", "sender_id": "ann", "return_url": return_url}

    sent = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=HEADERS)

    assert sent.status_code == 201
    assert len(stored["invites"]) == 1


@pytest.mark.parametrize("return_url", ["http://jobs.acme.com/next", "javascript:alert(1)"])
def test_a_return_address_off_https_invites_no_one(client, stored, return_url):
    body = {"email": "cara@example.com", "sender_id": "ann", "return_url": return_url}

    refused = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=HEADERS)

    assert refused.status_code == 422
    assert refused.json() == {"detail": RETURN_URL_INVALID, "code": "return_url_invalid"}
    assert stored["invites"] == []
