import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.auth.key_actor import key_actor
from fastapi import HTTPException
from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from companies.constants.ai_apps import AI_APPS_OFF, KEY_OTHER_COMPANY
from companies.constants.audit import VIA_ATS
from companies.constants.invites import COMPANY_SUSPENDED
from companies.repositories import companies, interviews, invites
from companies.services import candidate_invites
from companies.services import outbox as outbox_service

COMPANY = SimpleNamespace(
    id=uuid.uuid4(),
    name="Acme",
    suspended_at=None,
    ai_apps_off_at=None,
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
SECRET = "test-secret-that-is-at-least-32-bytes"
TOKEN = issue_token("ats", "companies", SECRET)
HEADERS = bearer(TOKEN)
ACCESS = f"/internal/companies/{COMPANY.id}/access"


@pytest.fixture(autouse=True)
def stored(monkeypatch):
    """The company and its two interviews; returns the invites sent and the outbox flushes."""
    calls = {"invites": [], "flushes": 0}

    async def get_company(session, company_id):
        return COMPANY if company_id == COMPANY.id else None

    async def get_interview(session, interview_id):
        return {READY.id: READY, MAKING.id: MAKING}.get(interview_id)

    async def by_ids(session, ids):
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

    async def find(session, interview_id, email):
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
        ("ann", {"member": True, "editor": True, "refused": None, "read_only": None}),
        ("bob", {"member": True, "editor": True, "refused": None, "read_only": None}),
        ("vic", {"member": True, "editor": False, "refused": None, "read_only": None}),
        ("eve", {"member": False, "editor": False, "refused": None, "read_only": None}),
    ],
)
def test_ats_asks_what_a_user_may_do_in_a_company(client, user_id, expected):
    response = client.get(f"{ACCESS}?user_id={user_id}", headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    ("via", "suspended", "ai_apps_off", "refused", "read_only"),
    [
        ("mcp", False, True, AI_APPS_OFF, None),
        # The in-app assistant isn't an AI app.
        ("assistant", False, True, None, None),
        (None, True, False, None, COMPANY_SUSPENDED),
    ],
)
def test_access_says_what_companies_own_routes_refuse(
    client, monkeypatch, via, suspended, ai_apps_off, refused, read_only
):
    now = datetime.now(UTC)
    monkeypatch.setattr(COMPANY, "suspended_at", now if suspended else None)
    monkeypatch.setattr(COMPANY, "ai_apps_off_at", now if ai_apps_off else None)
    headers = dict(HEADERS)

    if via:
        headers["X-Assistant"] = issue_token(via, "companies", SECRET)

    found = client.get(f"{ACCESS}?user_id=ann", headers=headers).json()

    assert (found["refused"], found["read_only"]) == (refused, read_only)


def test_an_api_keys_agent_is_refused_another_company(client):
    headers = {**HEADERS, "X-Assistant": issue_token("mcp", "companies", SECRET, {"company": "x"})}

    found = client.get(f"{ACCESS}?user_id=ann", headers=headers).json()

    assert found["refused"] == KEY_OTHER_COMPANY


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

    # Nothing new was made.
    assert response.status_code == 200
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
    assert response.status_code == (201 if sent else 200)
    assert bool(stored["invites"]) is sent


@pytest.mark.parametrize(
    ("interview_id", "code", "reason"),
    [(uuid.uuid4(), 404, None), (MAKING.id, 409, "interview_not_ready")],
)
def test_no_invite_to_an_interview_gone_or_not_ready(client, stored, interview_id, code, reason):
    body = {"email": "cara@example.com", "sender_id": "ann"}
    url = f"/internal/interviews/{interview_id}/invites"
    response = client.post(url, json=body, headers=HEADERS)

    assert (response.status_code, response.json().get("code")) == (code, reason)
    assert stored["invites"] == []


def test_the_api_invites_as_the_key_itself_never_a_member(client, stored):
    """The api service names the key acting (key_actor), which is no member of the company."""
    actor = key_actor(uuid.uuid4())
    body = {"email": "cara@example.com", "sender_id": actor}
    headers = {"Authorization": "Bearer " + issue_token("api", "companies", SECRET)}
    response = client.post(f"/internal/interviews/{READY.id}/invites", json=body, headers=headers)

    assert response.status_code == 201
    assert stored["invites"] == [(READY.id, COMPANY.id, actor, "cara@example.com", "api")]


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

    monkeypatch.setattr("prepza_common.limits.pause.is_paused", on)
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
