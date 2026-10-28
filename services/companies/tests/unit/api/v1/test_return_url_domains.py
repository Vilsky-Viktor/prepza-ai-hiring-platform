# The fixtures and the company are the internal ATS routes' tests'.
# ruff: noqa: F811
from companies.constants.allowed_domains import RETURN_URL_OFF_DOMAIN
from tests.unit.api.v1.test_internal_ats import (  # noqa: F401 (fixture)
    COMPANY,
    HEADERS,
    READY,
    stored,
)


def test_a_return_address_off_the_companys_allowed_domains_invites_no_one(
    client, stored, monkeypatch
):
    monkeypatch.setattr(COMPANY, "allowed_domains", ["*.acme.com"], raising=False)
    monkeypatch.setattr(COMPANY, "allow_localhost", False, raising=False)
    url = f"/internal/interviews/{READY.id}/invites"
    body = {"email": "cara@example.com", "sender_id": "ann"}

    refused = client.post(
        url, json={**body, "return_url": "https://elsewhere.com/next"}, headers=HEADERS
    )
    allowed = client.post(
        url, json={**body, "return_url": "https://jobs.acme.com/next"}, headers=HEADERS
    )

    assert refused.status_code == 422
    assert refused.json() == {"detail": RETURN_URL_OFF_DOMAIN, "code": "return_url_off_domain"}
    assert allowed.status_code == 201
    assert len(stored["invites"]) == 1


def test_a_return_address_depends_on_the_allowed_domains_not_verification(
    client, stored, monkeypatch
):
    monkeypatch.setattr(COMPANY, "verified_domain", "acme.com", raising=False)
    monkeypatch.setattr(COMPANY, "allowed_domains", ["jobs.acme.com"], raising=False)
    monkeypatch.setattr(COMPANY, "allow_localhost", False, raising=False)
    url = f"/internal/interviews/{READY.id}/invites"

    def invite(email, return_url):
        body = {"email": email, "sender_id": "ann", "return_url": return_url}

        return client.post(url, json=body, headers=HEADERS).status_code

    # The verified domain alone allows nothing; an allowed domain works unverified too.
    assert invite("a@example.com", "https://acme.com/next") == 422
    monkeypatch.setattr(COMPANY, "verified_domain", None, raising=False)
    assert invite("b@example.com", "https://jobs.acme.com/next") == 201
    # The developer's own computer only once the company allows it.
    assert invite("c@example.com", "http://localhost:3000/done") == 422
    monkeypatch.setattr(COMPANY, "allow_localhost", True, raising=False)
    assert invite("d@example.com", "http://localhost:3000/done") == 201
