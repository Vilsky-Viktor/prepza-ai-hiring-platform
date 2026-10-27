import uuid

from fastapi import HTTPException
from prepza_common.auth.encryption import decrypt

from app.config.settings import settings
from app.integrations import workable
from app.integrations.errors import KeyRejected
from app.services import ats as ats_service
from app.storage import ats
from tests.unit.workable_setup import COMPANY_ID, connect, sign_in


def test_without_an_encryption_key_integrations_are_off(client, stored, monkeypatch):
    monkeypatch.setattr(settings, "ats_encryption_key", "set-me")
    sign_in("ann")

    assert client.get(f"/connections?company_id={COMPANY_ID}").json()["available"] is False
    assert connect(client).status_code == 503


def test_an_admin_connects_and_the_key_is_kept_encrypted(client, stored, key):
    sign_in("ann")

    assert connect(client).status_code == 204

    saved = stored["connection"]
    assert saved.account == "acme"
    assert saved.member_id == "member-1"
    assert "good" not in saved.credentials
    assert decrypt(key, saved.credentials) == '{"subdomain": "acme", "token": "good"}'
    # Never the key itself.
    assert client.get(f"/connections?company_id={COMPANY_ID}").json()["connections"] == [
        {
            "provider": "workable",
            "account": "acme",
            "status": "connected",
            "created_at": saved.created_at.isoformat().replace("+00:00", "Z"),
        }
    ]


def test_a_refused_token_or_a_wrong_address_isnt_saved(client, stored, key):
    sign_in("ann")

    assert connect(client, token="bad").status_code == 422
    assert connect(client, account="not an address").status_code == 422
    assert stored["connection"] is None
    # A mistyped address isn't counted against the hourly connects; a refused token is.
    assert len(stored["connects"]) == 1


def test_a_viewer_sees_the_connection_but_changes_nothing(client, stored, key):
    sign_in("ann")
    connect(client)
    sign_in("vic")

    assert client.get(f"/connections?company_id={COMPANY_ID}").status_code == 200
    assert connect(client).status_code == 403
    assert client.delete(f"/workable?company_id={COMPANY_ID}").status_code == 403
    assert client.get(f"/workable/jobs?company_id={COMPANY_ID}").status_code == 403


def test_a_key_workable_stops_accepting_marks_the_connection_broken(
    client, stored, key, monkeypatch
):
    broken = []

    async def refuse(subdomain, token):
        raise KeyRejected

    async def mark_broken(connection_id):
        broken.append(connection_id)

    monkeypatch.setattr(workable, "jobs", refuse)
    monkeypatch.setattr(ats, "mark_broken", mark_broken)
    sign_in("ann")
    connect(client)

    response = client.get(f"/workable/jobs?company_id={COMPANY_ID}")

    assert response.status_code == 409
    assert broken == [stored["connection"].id]


def test_a_stranger_or_an_unknown_company_is_not_found(client, stored, key):
    sign_in("eve")

    assert client.get(f"/connections?company_id={COMPANY_ID}").status_code == 404
    assert client.get(f"/links?company_id={uuid.uuid4()}").status_code == 404
    assert connect(client).status_code == 404


def test_each_connect_is_counted_against_the_companys_hourly_limit(client, stored, key):
    sign_in("ann")
    connect(client)

    assert stored["connects"] == [
        (f"rate:ats-connects:{COMPANY_ID}", "ATS_CONNECTS_PER_HOUR", "ann")
    ]


def test_a_connect_past_the_limit_is_refused_before_the_ats_is_asked(
    client, stored, key, monkeypatch
):
    async def used_up(redis, key, name, message=None, **who):
        raise HTTPException(429, "Too many requests. Try again later.")

    asked = []

    async def check(account, token):
        asked.append(token)

    monkeypatch.setattr(ats_service, "hit_or_skip", used_up)
    monkeypatch.setattr(workable, "check", check)
    sign_in("ann")

    assert connect(client).status_code == 429
    assert asked == []
    assert stored["connection"] is None


def test_a_page_calling_the_ats_is_counted_per_company_and_refused_past_it_unasked(
    client, stored, key, monkeypatch
):
    sign_in("ann")
    connect(client)
    stored["connects"].clear()
    client.get(f"/workable/jobs?company_id={COMPANY_ID}")

    assert stored["connects"] == [
        (f"rate:ats-calls:{COMPANY_ID}", "ATS_CALLS_PER_COMPANY_MINUTE", "ann")
    ]

    async def used_up(redis, key, name, message=None, **who):
        raise HTTPException(429, "Too many requests. Try again later.")

    asked = []

    async def jobs(account, token):
        asked.append(token)

        return []

    monkeypatch.setattr(ats_service, "hit_or_skip", used_up)
    monkeypatch.setattr(workable, "jobs", jobs)

    assert client.get(f"/workable/jobs?company_id={COMPANY_ID}").status_code == 429
    assert asked == []


def test_ats_web_hooks_past_a_senders_limit_are_refused_before_their_signature(client, monkeypatch):
    from app.routers import ats_webhooks as hooks
    from app.services import ats_webhooks

    checked = []

    async def over(redis, key, name, message=None, **who):
        raise HTTPException(429, "Too many requests. Try again later.")

    async def receive(*args):
        checked.append(args)

    monkeypatch.setattr(hooks, "hit_or_skip", over)
    monkeypatch.setattr(ats_webhooks, "receive_breezy", receive)

    assert client.post(f"/webhooks/breezy/{uuid.uuid4()}", content=b"{}").status_code == 429
    assert checked == []
