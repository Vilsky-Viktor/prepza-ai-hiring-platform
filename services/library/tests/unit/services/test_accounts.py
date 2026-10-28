import asyncio
import re
from pathlib import Path

import httpx
import pytest
from fake_redis import FakeRedis
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.config.constants import ACCOUNT_OWNS_SHARED, GOOGLE_TIMEOUT_SECONDS
from prepza_common.http import http

from library.api.v1 import me as me_routes
from library.constants.accounts import ACCOUNT_CALL_TIMEOUT_SECONDS
from library.integrations import accounts as account_services
from library.main import app
from library.repositories import accounts, erasures
from library.services import accounts as account_service

USER = User(uid="ann", email="Ann@Example.com", email_verified=True, name="Ann")


@pytest.fixture
def steps(monkeypatch):
    """Records every deletion step, in order."""
    done = []

    async def delete_in(service, user_id, email):
        done.append(("service", service))

    async def delete_library(session, user_id):
        done.append(("library", user_id))

    async def remember(session, user_id, email):
        done.append(("erasure", user_id, email))

    monkeypatch.setattr(account_services, "delete_user", delete_in)
    monkeypatch.setattr(accounts, "delete_user", delete_library)
    monkeypatch.setattr(erasures, "record", remember)
    monkeypatch.setattr(
        account_service, "delete_sign_in", lambda uid: done.append(("sign-in", uid))
    )

    return done


def test_every_service_is_cleaned_before_the_sign_in_goes(steps):
    asyncio.run(account_service.delete_account(USER))

    # Companies first (it may refuse), then the others together.
    assert steps[0] == ("service", "companies")
    assert sorted(steps[1:9]) == [
        ("service", "accounts"),
        ("service", "api"),
        ("service", "assistant"),
        ("service", "ats"),
        ("service", "billing"),
        ("service", "generation"),
        ("service", "notifications"),
        ("service", "rounds"),
    ]
    assert steps[9:] == [
        ("library", "ann"),
        # Kept for the backups' life, to run again after a restore.
        ("erasure", "ann", "Ann@Example.com"),
        ("sign-in", "ann"),
    ]


def test_after_companies_the_other_services_delete_at_once(steps, monkeypatch):
    running, most = [0], [0]

    async def delete_in(service, user_id, email):
        running[0] += 1
        most[0] = max(most[0], running[0])
        await asyncio.sleep(0)
        running[0] -= 1

    monkeypatch.setattr(account_services, "delete_user", delete_in)

    asyncio.run(account_service.delete_account(USER))

    assert most[0] == len(account_services.services()) - 1


def test_a_failing_service_keeps_the_sign_in_so_the_user_can_retry(steps, monkeypatch):
    async def rounds_down(service, user_id, email):
        if service == "rounds":
            raise httpx.ConnectError("rounds is down")

        steps.append(("service", service))

    monkeypatch.setattr(account_services, "delete_user", rounds_down)

    with pytest.raises(httpx.ConnectError):
        asyncio.run(account_service.delete_account(USER))

    assert ("sign-in", "ann") not in steps


def test_an_owner_of_a_shared_company_is_told_to_hand_it_on_and_nothing_is_deleted(
    steps, monkeypatch
):
    """Companies goes first and refuses: no other service deletes anything, the sign-in stays."""

    async def refused(service, user_id, email):
        request = httpx.Request("DELETE", f"http://{service}/internal/users/{user_id}")
        response = httpx.Response(409, request=request)

        raise httpx.HTTPStatusError("refused", request=request, response=response)

    monkeypatch.setattr(account_services, "delete_user", refused)

    with pytest.raises(HTTPException) as error:
        asyncio.run(account_service.delete_account(USER))

    assert (error.value.status_code, error.value.detail) == (409, ACCOUNT_OWNS_SHARED)
    assert steps == []


@pytest.mark.parametrize("verified, sent", [(True, "Ann@Example.com"), (False, "")])
def test_candidate_data_is_matched_by_a_verified_email_only(monkeypatch, verified, sent):
    emails = set()

    async def delete_in(service, user_id, email):
        emails.add(email)

    async def export_from(service, user_id, email):
        emails.add(email)

        return {}

    async def nothing(session, user_id):
        return {}

    monkeypatch.setattr(account_services, "delete_user", delete_in)
    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(accounts, "delete_user", nothing)
    monkeypatch.setattr(accounts, "export", nothing)

    async def remember(session, user_id, email):
        pass

    monkeypatch.setattr(erasures, "record", remember)
    monkeypatch.setattr(account_service, "delete_sign_in", lambda uid: None)
    user = USER.model_copy(update={"email_verified": verified})

    asyncio.run(account_service.export_account(user))
    asyncio.run(account_service.delete_account(user))

    assert emails == {sent}


def test_the_export_holds_every_service_and_downloads_as_a_file(client, monkeypatch):
    async def export_from(service, user_id, email):
        return {"from": service}

    async def library_export(session, user_id):
        return {"question_votes": [], "question_reports": []}

    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(accounts, "export", library_export)
    monkeypatch.setattr(me_routes, "get_redis", lambda: FakeRedis())
    app.dependency_overrides[current_user] = lambda: USER

    try:
        response = client.get("/me/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="prepza-data.json"'
    assert response.json() == {
        "account": {
            "id": "ann",
            "email": "Ann@Example.com",
            "name": "Ann",
            "language": "en",
        },
        "library": {"question_votes": [], "question_reports": []},
        "companies": {"from": "companies"},
        "rounds": {"from": "rounds"},
        "generation": {"from": "generation"},
        "billing": {"from": "billing"},
        "notifications": {"from": "notifications"},
        "ats": {"from": "ats"},
        "api": {"from": "api"},
        "assistant": {"from": "assistant"},
        "accounts": {"from": "accounts"},
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

    asyncio.run(account_services.delete_user("ats", "ann", "ann@example.com"))
    asyncio.run(account_services.export_user("ats", "ann", "ann@example.com"))

    url = account_services.services()["ats"]
    body = b'{"email":"ann@example.com"}'

    assert sent == [
        ("DELETE", f"{url}/internal/users/ann", body),
        ("POST", f"{url}/internal/users/ann/export", body),
    ]


def test_deleting_and_exporting_in_a_service_waits_longer_than_an_ordinary_call(monkeypatch):
    from prepza_common.config.constants import HTTP_TIMEOUT_SECONDS

    from library.constants.accounts import ACCOUNT_CALL_TIMEOUT_SECONDS

    waits = []

    def answer(request):
        waits.append(request.extensions["timeout"]["read"])

        return httpx.Response(200, json={}, request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(answer))
    monkeypatch.setattr(http, "get_client", lambda: client)
    monkeypatch.setattr(account_services, "service_token", lambda service: "token")

    asyncio.run(account_services.delete_user("companies", "ann", "ann@example.com"))
    asyncio.run(account_services.export_user("rounds", "ann", "ann@example.com"))

    assert waits == [ACCOUNT_CALL_TIMEOUT_SECONDS] * 2
    assert ACCOUNT_CALL_TIMEOUT_SECONDS > HTTP_TIMEOUT_SECONDS


def test_data_downloads_past_the_hourly_limit_are_refused_before_asking_anyone(client, monkeypatch):
    asked = []

    async def export_from(service, user_id, email):
        asked.append(service)

        return {}

    async def library_export(session, user_id):
        return {}

    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(accounts, "export", library_export)
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


def test_a_deletion_fits_librarys_own_request_timeout():
    """Companies, then the others together, then the sign-in's revocation and deletion."""
    services_tf = (Path(__file__).resolve().parents[5] / "infra/terraform/locals.tf").read_text()
    library = int(
        re.search(r"^\s+library\s+= \{.*?timeout = (\d+)", services_tf, re.MULTILINE).group(1)
    )

    assert 2 * ACCOUNT_CALL_TIMEOUT_SECONDS + 2 * GOOGLE_TIMEOUT_SECONDS < library
