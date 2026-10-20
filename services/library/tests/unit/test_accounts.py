import asyncio

import httpx
import pytest
from fastapi import HTTPException
from prepza_common import http
from prepza_common.auth import current_user
from prepza_common.constants import ACCOUNT_OWNS_SHARED
from prepza_common.user import User

from app.integrations import accounts as account_services
from app.main import app
from app.services import accounts as account_service
from app.storage import accounts

USER = User(uid="ann", email="Ann@Example.com", email_verified=True, name="Ann")


@pytest.fixture
def steps(monkeypatch):
    """Records every deletion step, in order."""
    done = []

    async def delete_in(service, user_id, email):
        done.append(("service", service))

    async def delete_library(user_id):
        done.append(("library", user_id))

    monkeypatch.setattr(account_services, "delete_user", delete_in)
    monkeypatch.setattr(accounts, "delete_user", delete_library)
    monkeypatch.setattr(
        account_service, "delete_sign_in", lambda uid: done.append(("sign-in", uid))
    )

    return done


def test_every_service_is_cleaned_before_the_sign_in_goes(steps):
    asyncio.run(account_service.delete_account(USER))

    assert steps == [
        ("service", "companies"),
        ("service", "rounds"),
        ("service", "generation"),
        ("service", "billing"),
        ("service", "notifications"),
        ("service", "ats"),
        ("service", "api"),
        ("service", "assistant"),
        ("library", "ann"),
        ("sign-in", "ann"),
    ]


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

    async def nothing(user_id):
        return {}

    monkeypatch.setattr(account_services, "delete_user", delete_in)
    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(accounts, "delete_user", nothing)
    monkeypatch.setattr(accounts, "export", nothing)
    monkeypatch.setattr(account_service, "delete_sign_in", lambda uid: None)
    user = USER.model_copy(update={"email_verified": verified})

    asyncio.run(account_service.export_account(user))
    asyncio.run(account_service.delete_account(user))

    assert emails == {sent}


def test_the_export_holds_every_service_and_downloads_as_a_file(client, monkeypatch):
    async def export_from(service, user_id, email):
        return {"from": service}

    async def library_export(user_id):
        return {"question_votes": [], "question_reports": []}

    monkeypatch.setattr(account_services, "export_user", export_from)
    monkeypatch.setattr(accounts, "export", library_export)
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


def test_deleting_the_sign_in_revokes_it_first(monkeypatch):
    done = []
    monkeypatch.setattr(
        account_service.firebase_auth,
        "revoke_refresh_tokens",
        lambda uid: done.append(("revoked", uid)),
    )
    monkeypatch.setattr(
        account_service.firebase_auth, "delete_user", lambda uid: done.append(("deleted", uid))
    )

    account_service.delete_sign_in("ann")

    assert done == [("revoked", "ann"), ("deleted", "ann")]


def test_a_sign_in_already_gone_is_deleted(monkeypatch):
    def gone(uid):
        raise account_service.firebase_auth.UserNotFoundError("gone")

    monkeypatch.setattr(account_service.firebase_auth, "revoke_refresh_tokens", gone)

    account_service.delete_sign_in("ann")
