from types import SimpleNamespace

import pytest
from fake_redis import FakeRedis
from firebase_admin import auth as firebase_auth
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

import companies.api.v1.invites as routes
from companies.constants.invites import INVITE_EXPIRED, NOT_THE_GUEST, InviteStatus
from companies.main import app
from companies.services import candidate_start, invite_pages
from tests.unit.api.v1.test_invites import (  # noqa: F401 (fixtures)
    INVITE_ID,
    invite_page,
    stored_invite,
)

GUEST = f"guest-{INVITE_ID}"


def sign_in(uid, email=""):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=email, email_verified=bool(email)
    )


@pytest.fixture
def guest_invite(monkeypatch, invite_page):  # noqa: F811
    """The invite a company's platform sent with sign_in false, its candidate in it already, and
    the sessions it starts recorded instead of made."""
    invite_page.guest = True
    invite_page.status = InviteStatus.IN_PROCESS
    started = []

    async def start(invite, interview, user):
        started.append(user.uid)

        return {"sessions": []}

    monkeypatch.setattr(candidate_start, "start_sessions", start)
    monkeypatch.setattr(
        firebase_auth, "create_custom_token", lambda uid: f"custom-for-{uid}".encode()
    )

    return started


def test_a_guest_invitation_says_so_and_signs_its_link_in(client, guest_invite):
    assert client.get("/invites/token-1").json()["guest"] is True

    response = client.post("/invites/token-1/guest")

    assert response.status_code == 200
    assert response.json() == {"token": f"custom-for-{GUEST}"}


def test_an_invitation_by_email_has_no_guest_sign_in(client, invite_page):  # noqa: F811
    assert client.get("/invites/token-1").json()["guest"] is False
    assert client.post("/invites/token-1/guest").status_code == 404


def test_an_expired_guest_invitation_signs_no_one_in(
    client,
    guest_invite,
    invite_page,  # noqa: F811
):
    invite_page.status = InviteStatus.EXPIRED

    # Gone, saying the company can send it again: on the invitation and for its sign-in.
    for response in (client.get("/invites/token-1"), client.post("/invites/token-1/guest")):
        assert response.status_code == 410
        assert response.json()["detail"] == INVITE_EXPIRED


def test_the_guest_starts_without_an_email(client, guest_invite):
    sign_in(GUEST)

    assert client.post("/invites/token-1/start").status_code == 200
    assert guest_invite == [GUEST]


def test_only_the_guest_starts_a_guest_invitation_not_even_the_invited_email(client, guest_invite):
    sign_in("bob", "bob@example.com")
    response = client.post("/invites/token-1/start")

    assert response.status_code == 403
    assert response.json()["detail"] == NOT_THE_GUEST
    assert guest_invite == []


def embedding(monkeypatch, **changes) -> SimpleNamespace:
    """The invite's company, with no allowed domains unless `changes` say so."""
    acme = SimpleNamespace(
        **{
            "name": "Acme",
            "verified_domain": None,
            "allowed_domains": [],
            "allow_localhost": False,
            "brand_colors": None,
            "brand_heading_font": None,
            "brand_text_font": None,
            "brand_radius": None,
            "brand_button_radius": None,
            "suspended_at": None,
            **changes,
        }
    )

    async def company(session, company_id):
        return acme

    monkeypatch.setattr(invite_pages.companies, "get", company)
    monkeypatch.setattr(invite_pages, "logo_path", lambda company: None)

    return acme


def test_only_a_guest_invitation_may_be_embedded_and_only_on_the_companys_allowed_domains(
    client,
    monkeypatch,
    invite_page,  # noqa: F811
):
    acme = embedding(monkeypatch, verified_domain="acme.com")

    def ancestors(query=""):
        return client.get(f"/invites/token-1{query}").json()["embed_ancestors"]

    acme.allowed_domains = ["jobs.acme.com"]

    # An invite sent by email is never embedded.
    assert ancestors() == []

    invite_page.guest = True

    assert ancestors() == ["jobs.acme.com"]
    # Verification has nothing to do with it: no allowed domains, no site, verified or not.
    acme.allowed_domains = []

    assert ancestors() == []

    acme.allowed_domains, acme.verified_domain = ["jobs.acme.com"], None

    assert ancestors() == ["jobs.acme.com"]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("?embed_origin=https://jobs.acme.com", ["jobs.acme.com"]),
        ("?embed_origin=https://evil.com", []),
        # The browser holds the scheme to the policy's; a claim is checked by its host.
        ("?embed_origin=http://jobs.acme.com", ["jobs.acme.com"]),
        ("?embed_referrer=https://evil.com/page", []),
        (
            "?embed_origin=https://jobs.acme.com&embed_referrer=https://jobs.acme.com/apply",
            ["jobs.acme.com"],
        ),
        ("?embed_origin=http://localhost:3000", []),
    ],
)
def test_a_page_off_the_allowed_domains_gets_no_sources(
    client,
    monkeypatch,
    invite_page,  # noqa: F811
    query,
    expected,
):
    embedding(monkeypatch, allowed_domains=["jobs.acme.com"])
    invite_page.guest = True

    assert client.get(f"/invites/token-1{query}").json()["embed_ancestors"] == expected


def test_localhost_may_embed_once_the_company_opts_in(
    client,
    monkeypatch,
    invite_page,  # noqa: F811
):
    embedding(monkeypatch, allow_localhost=True)
    invite_page.guest = True
    found = client.get("/invites/token-1?embed_origin=http://localhost:3000").json()

    assert "http://localhost:*" in found["embed_ancestors"]


def test_guest_sign_ins_past_the_hourly_limit_of_an_address_are_refused(
    client, guest_invite, monkeypatch
):
    redis = FakeRedis({"GUEST_SIGN_INS_PER_IP_HOUR": 2})
    monkeypatch.setattr(routes, "get_redis", lambda: redis)

    codes = [client.post("/invites/token-1/guest").status_code for _ in range(3)]

    assert codes == [200, 200, 429]
