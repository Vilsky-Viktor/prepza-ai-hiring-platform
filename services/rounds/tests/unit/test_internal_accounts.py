from prepza_common.service_auth import issue_token

from app.storage import accounts

HEADERS = {
    "Authorization": "Bearer "
    + issue_token("library", "rounds", "test-secret-that-is-at-least-32-bytes")
}


def test_library_exports_a_users_sessions_with_a_post(client, monkeypatch):
    async def export(user_id):
        return {"interview_sections": [user_id]}

    monkeypatch.setattr(accounts, "export", export)

    response = client.post("/internal/users/ann/export", headers=HEADERS)

    assert response.json() == {"interview_sections": ["ann"]}


def test_notifications_reads_the_candidates_or_the_learners_a_page_at_a_time(client, monkeypatch):
    asked = []

    async def user_ids(practice, after, limit):
        asked.append((practice, after, limit))

        return ["ann"]

    monkeypatch.setattr(accounts, "user_ids", user_ids)
    headers = {
        "Authorization": "Bearer "
        + issue_token("notifications", "rounds", "test-secret-that-is-at-least-32-bytes")
    }

    learners = client.get(
        "/internal/users/ids",
        params={"group": "learners", "after": "a", "limit": 5},
        headers=headers,
    )
    candidates = client.get("/internal/users/ids", params={"group": "candidates"}, headers=headers)

    assert learners.json() == candidates.json() == {"user_ids": ["ann"]}
    assert asked == [(True, "a", 5), (False, "", 5000)]
    assert (
        client.get("/internal/users/ids", params={"group": "everyone"}, headers=headers).status_code
        == 422
    )
    assert client.get("/internal/users/ids", params={"group": "learners"}).status_code in (401, 403)
