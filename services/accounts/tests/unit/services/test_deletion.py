import asyncio
import re
from pathlib import Path

import httpx
import pytest
from fake_redis import FakeRedis
from fastapi import HTTPException
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.config.constants import ACCOUNT_OWNS_SHARED, GOOGLE_TIMEOUT_SECONDS
from testee_common.config.event_constants import PUBLISH_IN_REQUEST_TIMEOUT_SECONDS
from testee_common.events.deletions import USER_DELETED
from testee_common.http import http

from accounts.api.v1 import me as me_routes
from accounts.constants.accounts import ACCOUNT_CALL_TIMEOUT_SECONDS
from accounts.integrations import services as account_services
from accounts.main import app
from accounts.repositories import erasures, outbox, user_data
from accounts.services import deletion as account_service
from accounts.services import erasures as replays
from accounts.services import outbox as outbox_service
from tests.unit.sessions import FakeSessions

USER = User(uid="ann", email="Ann@Example.com", email_verified=True, name="Ann")


@pytest.fixture
def steps(monkeypatch):
    """Records every deletion step, in order."""
    done = []

    async def delete_in_companies(user_id, email):
        done.append(("companies", user_id, email))

    async def delete_own(session, user_id):
        done.append(("own", user_id))

    async def remember(session, user_id, email):
        done.append(("erasure", user_id, email))

    async def flushed():
        done.append("published")

    monkeypatch.setattr(account_services, "delete_in_companies", delete_in_companies)
    monkeypatch.setattr(user_data, "delete_user", delete_own)
    monkeypatch.setattr(erasures, "record", remember)
    monkeypatch.setattr(
        outbox, "add", lambda session, kind, data: done.append(("event", kind, data))
    )
    monkeypatch.setattr(outbox_service, "flush_quietly", flushed)
    monkeypatch.setattr(replays, "Session", FakeSessions())
    monkeypatch.setattr(
        account_service, "delete_sign_in", lambda uid: done.append(("sign-in", uid))
    )

    return done


def test_companies_deletes_first_then_one_save_tells_every_other_holder_then_the_sign_in_goes(
    steps,
):
    asyncio.run(account_service.delete_account(USER))

    assert steps == [
        # Companies first, by a call: it may refuse.
        ("companies", "ann", "Ann@Example.com"),
        # One save: accounts' rows, the note kept for the backups' life to run again after a
        # restore, and the event every other holder deletes its part by.
        ("own", "ann"),
        ("erasure", "ann", "Ann@Example.com"),
        ("event", USER_DELETED, {"user_id": "ann", "email": "Ann@Example.com"}),
        "published",
        ("sign-in", "ann"),
    ]


def test_companies_failing_keeps_the_sign_in_and_tells_no_one_so_the_user_can_retry(
    steps, monkeypatch
):
    async def companies_down(user_id, email):
        raise httpx.ConnectError("companies is down")

    monkeypatch.setattr(account_services, "delete_in_companies", companies_down)

    with pytest.raises(httpx.ConnectError):
        asyncio.run(account_service.delete_account(USER))

    assert steps == []


def test_an_owner_of_a_shared_company_is_told_to_hand_it_on_and_nothing_is_deleted(
    steps, monkeypatch
):
    """Companies goes first and refuses: nothing is deleted, no event, the sign-in stays."""

    async def refused(user_id, email):
        request = httpx.Request("DELETE", f"http://companies/internal/users/{user_id}")
        response = httpx.Response(409, request=request)

        raise httpx.HTTPStatusError("refused", request=request, response=response)

    monkeypatch.setattr(account_services, "delete_in_companies", refused)

    with pytest.raises(HTTPException) as error:
        asyncio.run(account_service.delete_account(USER))

    assert (error.value.status_code, error.value.detail) == (409, ACCOUNT_OWNS_SHARED)
    assert steps == []


@pytest.mark.parametrize("verified, sent", [(True, "Ann@Example.com"), (False, "")])
def test_candidate_data_is_matched_by_a_verified_email_only(steps, monkeypatch, verified, sent):
    emails = set()

    async def delete_in(user_id, email):
        emails.add(email)

    async def export_from(service, user_id, email):
        emails.add(email)

        return {}

    async def nothing(session, user_id):
        return {}

    monkeypatch.setattr(account_services, "delete_in_companies", delete_in)
    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(user_data, "export", nothing)
    user = USER.model_copy(update={"email_verified": verified})

    asyncio.run(account_service.export_account(user))
    asyncio.run(account_service.delete_account(user))
    emails |= {step[2]["email"] for step in steps if step[0] == "event"}

    assert emails == {sent}


def test_the_export_holds_every_service_and_downloads_as_a_file(client, monkeypatch):
    async def export_from(service, user_id, email):
        return {"from": service}

    async def own_export(session, user_id):
        return {"terms_accepted": []}

    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(user_data, "export", own_export)
    monkeypatch.setattr(me_routes, "get_redis", lambda: FakeRedis())
    app.dependency_overrides[current_user] = lambda: USER

    try:
        response = client.get("/me/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="testee-data.json"'
    assert response.json() == {
        "account": {
            "id": "ann",
            "email": "Ann@Example.com",
            "name": "Ann",
            "language": "en",
        },
        "accounts": {"terms_accepted": []},
        "companies": {"from": "companies"},
        "rounds": {"from": "rounds"},
        "generation": {"from": "generation"},
        "billing": {"from": "billing"},
        "notifications": {"from": "notifications"},
        "ats": {"from": "ats"},
        "api": {"from": "api"},
        "assistant": {"from": "assistant"},
        "library": {"from": "library"},
        "site": {"from": "site"},
    }


def test_deletion_and_export_send_the_email_in_the_body_not_the_url(monkeypatch):
    """Request logs record URLs, so the email never goes in the query string."""
    sent = []

    def handler(request):
        sent.append((request.method, str(request.url), request.content))

        return httpx.Response(200, json={})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(http, "get_client", lambda: client)
    monkeypatch.setattr(account_services, "service_token", lambda callee: "token")

    asyncio.run(account_services.delete_in_companies("ann", "ann@example.com"))
    asyncio.run(account_services.export_user("ats", "ann", "ann@example.com"))

    companies = account_services.services()["companies"]
    ats = account_services.services()["ats"]
    body = b'{"email":"ann@example.com"}'

    assert sent == [
        ("DELETE", f"{companies}/internal/users/ann", body),
        ("POST", f"{ats}/internal/users/ann/export", body),
    ]


def test_deleting_and_exporting_in_a_service_waits_longer_than_an_ordinary_call(monkeypatch):
    from testee_common.config.constants import HTTP_TIMEOUT_SECONDS

    from accounts.constants.accounts import ACCOUNT_CALL_TIMEOUT_SECONDS

    waits = []

    def answer(request):
        waits.append(request.extensions["timeout"]["read"])

        return httpx.Response(200, json={}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)
    monkeypatch.setattr(account_services, "service_token", lambda service: "token")

    asyncio.run(account_services.delete_in_companies("ann", "ann@example.com"))
    asyncio.run(account_services.export_user("rounds", "ann", "ann@example.com"))

    assert waits == [ACCOUNT_CALL_TIMEOUT_SECONDS] * 2
    assert ACCOUNT_CALL_TIMEOUT_SECONDS > HTTP_TIMEOUT_SECONDS


def test_data_downloads_past_the_hourly_limit_are_refused_before_asking_anyone(client, monkeypatch):
    asked = []

    async def export_from(service, user_id, email):
        asked.append(service)

        return {}

    async def own_export(session, user_id):
        return {}

    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(user_data, "export", own_export)
    redis = FakeRedis({"DATA_EXPORTS_PER_HOUR": 1})
    monkeypatch.setattr(me_routes, "get_redis", lambda: redis)
    app.dependency_overrides[current_user] = lambda: USER

    try:
        first = client.get("/me/export")
        asked_once = len(asked)
        second = client.get("/me/export")
    finally:
        app.dependency_overrides.clear()

    assert (first.status_code, second.status_code) == (200, 429)
    assert len(asked) == asked_once


def test_a_deletion_fits_accounts_own_request_timeout():
    """Companies' call, the event's quick publish, then the sign-in's revocation and deletion."""
    services_tf = (Path(__file__).resolve().parents[5] / "infra/terraform/locals.tf").read_text()
    accounts = int(
        re.search(r"^\s+accounts\s+= \{.*?timeout = (\d+)", services_tf, re.MULTILINE).group(1)
    )

    assert (
        ACCOUNT_CALL_TIMEOUT_SECONDS
        + PUBLISH_IN_REQUEST_TIMEOUT_SECONDS
        + 2 * GOOGLE_TIMEOUT_SECONDS
        < accounts
    )
