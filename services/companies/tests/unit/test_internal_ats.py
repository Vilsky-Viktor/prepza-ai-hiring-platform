import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from prepza_common.http import bearer
from prepza_common.service_auth import issue_token

from app.constants.audit import VIA_ATS
from app.constants.invites import RETURN_URL_OFF_DOMAIN
from app.services import candidate_invites
from app.services import outbox as outbox_service
from app.storage import companies, interviews, invites

COMPANY = SimpleNamespace(
    id=uuid.uuid4(),
    name="Acme",
    members=[
        SimpleNamespace(user_id="ann", role="owner"),
        SimpleNamespace(user_id="bob", role="admin"),
        SimpleNamespace(user_id="vic", role="viewer"),
    ],
)
READY = SimpleNamespace(
    id=uuid.uuid4(), company_id=COMPANY.id, title="Backend", set_id=uuid.uuid4()
)
MAKING = SimpleNamespace(id=uuid.uuid4(), company_id=COMPANY.id, title=None, set_id=None)
TOKEN = issue_token("ats", "companies", "test-secret-that-is-at-least-32-bytes")
HEADERS = bearer(TOKEN)
ACCESS = f"/internal/companies/{COMPANY.id}/access"


@pytest.fixture(autouse=True)
def stored(monkeypatch):
    """The company and its two interviews; returns the invites sent and the outbox flushes."""
    calls = {"invites": [], "flushes": 0}

    async def get_company(company_id):
        return COMPANY if company_id == COMPANY.id else None

    async def get_interview(interview_id):
        return {READY.id: READY, MAKING.id: MAKING}.get(interview_id)

    async def by_ids(ids):
        return [item for item in (READY, MAKING) if item.id in ids]

    async def invite(
        interview,
        company,
        user,
        email,
        name=None,
        return_url=None,
        sign_in=True,
        theme=None,
        via=None,
    ):
        calls["invites"].append((interview.id, company.id, user.uid, email, via))
        calls.setdefault("names", []).append(name)

        return SimpleNamespace(id=uuid.UUID(int=7))

    async def flush():
        calls["flushes"] += 1

    async def find(interview_id, email):
        return calls.get("found")

    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(interviews, "get", get_interview)
    monkeypatch.setattr(interviews, "by_ids", by_ids)
    monkeypatch.setattr(candidate_invites, "invite", invite)
    monkeypatch.setattr(outbox_service, "flush_quietly", flush)
    monkeypatch.setattr(invites, "find", find)

    return calls


@pytest.mark.parametrize(
    ("user_id", "expected"),
    [
        ("ann", {"member": True, "editor": True}),
        ("bob", {"member": True, "editor": True}),
        ("vic", {"member": True, "editor": False}),
        ("eve", {"member": False, "editor": False}),
    ],
)
def test_ats_asks_what_a_user_may_do_in_a_company(client, user_id, expected):
    response = client.get(f"{ACCESS}?user_id={user_id}", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == expected


def test_a_company_that_doesnt_exist_is_not_found(client):
    url = f"/internal/companies/{uuid.uuid4()}/access?user_id=ann"

    assert client.get(url, headers=HEADERS).status_code == 404


def test_ats_gets_the_interviews_that_still_exist(client):
    gone = uuid.uuid4()
    url = f"/internal/interviews?ids={READY.id}&ids={MAKING.id}&ids={gone}"

    assert client.get(url, headers=HEADERS).json() == [
        {"id": str(READY.id), "company_id": str(COMPANY.id), "title": "Backend", "ready": True},
        {"id": str(MAKING.id), "company_id": str(COMPANY.id), "title": None, "ready": False},
    ]


def test_ats_invites_a_candidate_as_the_member_who_connected_it(client, stored):
    body = {"email": "Cara@example.com", "sender_id": "ann"}
    response = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=HEADERS)

    assert response.status_code == 201
    assert response.json() == {"invite_id": str(uuid.UUID(int=7)), "created": True}
    # The action log shows it came through the ATS.
    assert stored["invites"] == [(READY.id, COMPANY.id, "ann", "Cara@example.com", VIA_ATS)]
    assert stored["flushes"] == 1


def test_a_candidate_who_finished_is_returned_without_another_email(client, stored):
    stored["found"] = SimpleNamespace(id=uuid.UUID(int=9), status="finished")
    body = {"email": "cara@example.com", "sender_id": "ann"}
    response = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=HEADERS)

    assert response.status_code == 201
    assert response.json() == {"invite_id": str(uuid.UUID(int=9)), "created": False}
    assert stored["invites"] == []


@pytest.mark.parametrize(
    ("status", "resend", "sent"),
    [
        ("invited", False, False),
        ("undelivered", False, False),
        ("in_process", False, False),
        ("expired", False, True),
        ("invited", True, True),
    ],
)
def test_without_resend_a_candidate_still_invited_is_returned_as_they_are(
    client, stored, status, resend, sent
):
    """The API's retries: the same candidate, no second email; an expired invite is sent again,
    and an ATS (resend) sends an open one again as before."""
    stored["found"] = SimpleNamespace(id=uuid.UUID(int=9), status=status)
    body = {"email": "cara@example.com", "sender_id": "ann", "resend": resend}
    response = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=HEADERS)

    assert response.json()["created"] is sent
    assert bool(stored["invites"]) is sent


@pytest.mark.parametrize(("interview_id", "code"), [(uuid.uuid4(), 404), (MAKING.id, 409)])
def test_no_invite_to_an_interview_gone_or_not_ready(client, stored, interview_id, code):
    body = {"email": "cara@example.com", "sender_id": "ann"}
    url = f"/internal/interviews/{interview_id}/invites"

    assert client.post(url, json=body, headers=HEADERS).status_code == code
    assert stored["invites"] == []


@pytest.mark.parametrize("sender", ["vic", "eve"])
def test_a_viewer_or_a_removed_member_invites_no_one(client, stored, sender):
    body = {"email": "cara@example.com", "sender_id": sender}
    url = f"/internal/interviews/{READY.id}/invites"
    response = client.post(url, json=body, headers=HEADERS)

    assert response.status_code == 403
    assert stored["invites"] == []


def test_no_invite_during_the_pause(client, stored, monkeypatch):
    async def on(redis):
        return True

    monkeypatch.setattr("prepza_common.pause.is_paused", on)
    body = {"email": "cara@example.com", "sender_id": "ann"}
    url = f"/internal/interviews/{READY.id}/invites"

    assert client.post(url, json=body, headers=HEADERS).status_code == 503
    assert stored["invites"] == []


@pytest.mark.parametrize("code", [402, 429])
def test_a_refused_invite_answers_with_its_refusal(client, monkeypatch, code):
    async def refuse(*args, **kwargs):
        raise HTTPException(code, "Refused")

    monkeypatch.setattr(candidate_invites, "invite", refuse)
    body = {"email": "cara@example.com", "sender_id": "ann"}
    url = f"/internal/interviews/{READY.id}/invites"

    assert client.post(url, json=body, headers=HEADERS).status_code == code


def test_the_ats_routes_need_a_service_token(client):
    body = {"email": "cara@example.com", "sender_id": "ann"}

    assert client.get(f"{ACCESS}?user_id=ann").status_code in (401, 403)
    assert client.get(f"/internal/interviews?ids={READY.id}").status_code in (401, 403)
    assert client.post(f"/internal/interviews/{READY.id}/invites", json=body).status_code in (
        401,
        403,
    )


def test_the_ats_name_goes_with_the_invite(client, stored):
    body = {"email": "cara@example.com", "sender_id": "ann", "name": "Cara Diaz"}
    response = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=HEADERS)

    assert response.status_code == 201
    assert stored["names"] == ["Cara Diaz"]


def test_a_return_address_off_the_companys_website_invites_no_one(client, stored, monkeypatch):
    monkeypatch.setattr(COMPANY, "verified_domain", "acme.com", raising=False)
    url = f"/internal/interviews/{READY.id}/invites"
    body = {"email": "cara@example.com", "sender_id": "ann"}

    refused = client.post(
        url, json={**body, "return_url": "https://elsewhere.com/next"}, headers=HEADERS
    )
    allowed = client.post(
        url, json={**body, "return_url": "https://jobs.acme.com/next"}, headers=HEADERS
    )

    assert refused.status_code == 422
    assert refused.json()["detail"] == RETURN_URL_OFF_DOMAIN
    assert allowed.status_code == 201
    assert len(stored["invites"]) == 1


def test_a_return_address_needs_the_company_verified_not_only_its_website(
    client, stored, monkeypatch
):
    monkeypatch.setattr(COMPANY, "website_domain", "acme.com", raising=False)
    monkeypatch.setattr(COMPANY, "verified_domain", None, raising=False)
    body = {"email": "cara@example.com", "sender_id": "ann", "return_url": "https://acme.com/next"}
    response = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=HEADERS)

    assert response.status_code == 422
    assert stored["invites"] == []
