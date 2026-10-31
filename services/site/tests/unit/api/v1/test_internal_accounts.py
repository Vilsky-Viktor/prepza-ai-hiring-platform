"""Accounts' `user.deleted` deletes, and accounts' export call reads, a user's data here: the
contact messages sent from their email (in the body, so request logs don't record it). Only
accounts, with site's key, may ask for an export."""

from event_pushes import push
from testee_common.auth.service_auth import issue_token
from testee_common.http.http import bearer

from site_content.services import accounts

FROM_ACCOUNTS = bearer(issue_token("accounts", "site", "test-secret-that-is-at-least-32-bytes"))


def test_a_deleted_account_takes_its_contact_messages_by_email(client, monkeypatch):
    deleted = []

    async def remove(email):
        deleted.append(email)

    monkeypatch.setattr(accounts, "remove_user", remove)

    gone = push("user.deleted", {"user_id": "u1", "email": "Ann@Example.com"})
    response = client.post("/internal/events", json=gone)
    ignored = client.post("/internal/events", json=push("company.deleted", {}))
    malformed = client.post("/internal/events", json=push("user.deleted", {}))

    assert (response.status_code, ignored.status_code, malformed.status_code) == (204, 204, 204)
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
