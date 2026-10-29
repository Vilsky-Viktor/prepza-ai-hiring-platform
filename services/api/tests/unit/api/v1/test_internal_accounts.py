from event_pushes import push
from prepza_common.auth.service_auth import issue_token

from api.repositories import keys, webhook_retries, webhooks

HEADERS = {
    "Authorization": "Bearer "
    + issue_token("accounts", "api", "test-secret-that-is-at-least-32-bytes")
}


async def nothing(session, user_id):
    return []


def test_a_deleted_account_leaves_its_keys_and_web_hooks_takes_waiting_results_and_exports(
    client, monkeypatch
):
    removed = []

    async def forget_user(session, user_id):
        removed.append(("forgotten", user_id))

    monkeypatch.setattr(keys, "forget_user", forget_user)
    monkeypatch.setattr(webhooks, "forget_user", forget_user)
    monkeypatch.setattr(keys, "of_user", nothing)
    monkeypatch.setattr(webhooks, "of_user", nothing)

    async def remove_email(session, email):
        removed.append(("removed", email))

    monkeypatch.setattr(webhook_retries, "remove_email", remove_email)

    deleted = client.post(
        "/internal/events",
        json=push("user.deleted", {"user_id": "ann", "email": "ann@example.com"}),
    )
    exported = client.post(
        "/internal/users/ann/export", json={"email": "ann@example.com"}, headers=HEADERS
    )

    assert deleted.status_code == 204
    # Their keys and web hooks stay the company's, without their id; their results as a
    # candidate waiting to be sent again go.
    assert removed == [("forgotten", "ann"), ("forgotten", "ann"), ("removed", "ann@example.com")]
    assert exported.json() == {"api_keys": [], "webhooks": []}
