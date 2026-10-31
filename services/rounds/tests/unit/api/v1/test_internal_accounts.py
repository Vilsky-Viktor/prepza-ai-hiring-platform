from testee_common.auth.service_auth import issue_token

from rounds.repositories import accounts, open_to_offers

HEADERS = {
    "Authorization": "Bearer "
    + issue_token("library", "rounds", "test-secret-that-is-at-least-32-bytes")
}


def test_library_exports_a_users_sessions_with_a_post(client, monkeypatch):
    asked = []

    async def of_user(session, user_id):
        asked.append(user_id)

        return []

    async def not_open(session, user_id):
        asked.append(user_id)

    async def no_consents(session, user_id):
        asked.append(user_id)

        return []

    monkeypatch.setattr(accounts, "of_user", of_user)
    monkeypatch.setattr(open_to_offers, "get", not_open)
    monkeypatch.setattr(open_to_offers, "consents", no_consents)

    response = client.post("/internal/users/ann/export", headers=HEADERS)

    assert asked == ["ann", "ann", "ann"]
    assert response.json() == {
        "interview_sections": [],
        "open_to_offers": None,
        "open_to_offers_changes": [],
    }


def test_notifications_reads_the_candidates_or_the_learners_a_page_at_a_time(client, monkeypatch):
    asked = []

    async def user_ids(session, practice, after, limit):
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
