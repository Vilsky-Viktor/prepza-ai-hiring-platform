"""Accounts deletes and exports a user's data here: the contact messages sent from their email,
in the body so request logs don't record it. Only accounts, with site's key, may ask."""

from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from site_content.services import accounts

FROM_ACCOUNTS = bearer(issue_token("accounts", "site", "test-secret-that-is-at-least-32-bytes"))


def test_deleting_a_user_deletes_their_contact_messages_by_email(client, monkeypatch):
    deleted = []

    async def remove(email):
        deleted.append(email)

    monkeypatch.setattr(accounts, "remove_user", remove)

    response = client.request(
        "DELETE", "/internal/users/u1", json={"email": "Ann@Example.com"}, headers=FROM_ACCOUNTS
    )

    assert response.status_code == 204
    assert deleted == ["Ann@Example.com"]


def test_a_users_export_holds_their_contact_messages(client, monkeypatch):
    async def export(email):
        return {"contact_messages": [{"name": "Ann", "email": email, "message": "Hi"}]}

    monkeypatch.setattr(accounts, "export_user", export)

    response = client.post(
        "/internal/users/u1/export", json={"email": "ann@example.com"}, headers=FROM_ACCOUNTS
    )

    assert response.json() == {
        "contact_messages": [{"name": "Ann", "email": "ann@example.com", "message": "Hi"}]
    }


def test_only_another_service_may_delete_or_export_a_user(client):
    body = {"email": "ann@example.com"}

    assert client.request("DELETE", "/internal/users/u1", json=body).status_code == 401
    assert client.post("/internal/users/u1/export", json=body).status_code == 401
