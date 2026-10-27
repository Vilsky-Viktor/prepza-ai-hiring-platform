from prepza_common.auth.service_auth import issue_token

from app.storage import keys, webhook_retries, webhooks

HEADERS = {
    "Authorization": "Bearer "
    + issue_token("library", "api", "test-secret-that-is-at-least-32-bytes")
}


async def nothing(user_id):
    return []


def test_library_deletes_and_exports_a_users_keys_web_hooks_and_waiting_results(
    client, monkeypatch
):
    removed = []

    async def remove_user(user_id):
        removed.append(user_id)

    monkeypatch.setattr(keys, "remove_user", remove_user)
    monkeypatch.setattr(webhooks, "remove_user", remove_user)
    monkeypatch.setattr(keys, "of_user", nothing)
    monkeypatch.setattr(webhooks, "of_user", nothing)

    async def remove_email(email):
        removed.append(email)

    monkeypatch.setattr(webhook_retries, "remove_email", remove_email)

    deleted = client.request(
        "DELETE", "/internal/users/ann", json={"email": "ann@example.com"}, headers=HEADERS
    )
    exported = client.post(
        "/internal/users/ann/export", json={"email": "ann@example.com"}, headers=HEADERS
    )

    assert deleted.status_code == 204
    # Their keys and web hooks, and their results as a candidate waiting to be sent again.
    assert removed == ["ann", "ann", "ann@example.com"]
    assert exported.json() == {"api_keys": [], "webhooks": []}
