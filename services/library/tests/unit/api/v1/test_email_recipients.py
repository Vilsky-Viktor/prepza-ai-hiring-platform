from types import SimpleNamespace

from firebase_admin import auth as firebase_auth
from prepza_common.http.http import bearer

from library.constants.emails import DEFAULTS
from library.repositories import emails
from tests.unit.api.v1.test_internal import token

HEADERS = bearer(token())


def account(uid, email, language=None, disabled=False):
    claims = {"language": language} if language else None

    return SimpleNamespace(uid=uid, email=email, custom_claims=claims, disabled=disabled)


def test_recipients_have_their_address_language_and_preferences(client, monkeypatch):
    looked_up = []

    def get_users(identifiers):
        looked_up.append([identifier.uid for identifier in identifiers])

        return SimpleNamespace(
            users=[
                account("ann", "ann@example.com", "de"),
                account("bob", "bob@example.com", "xx"),
                account("off", "off@example.com", disabled=True),
                account("phone", None),
            ]
        )

    async def preferences_of(session, user_ids):
        return {user_id: {**DEFAULTS, "reminders": user_id != "bob"} for user_id in user_ids}

    monkeypatch.setattr(firebase_auth, "get_users", get_users)
    monkeypatch.setattr(emails, "preferences_of", preferences_of)

    response = client.post(
        "/internal/users/email-recipients",
        json={"user_ids": ["ann", "bob", "off", "phone", "gone"]},
        headers=HEADERS,
    )
    found = response.json()["recipients"]

    assert looked_up == [["ann", "bob", "off", "phone", "gone"]]
    # Gone, disabled or without an email: left out. An unknown language is English.
    assert [(item["user_id"], item["email"], item["language"]) for item in found] == [
        ("ann", "ann@example.com", "de"),
        ("bob", "bob@example.com", "en"),
    ]
    assert found[1]["preferences"]["reminders"] is False


def test_firebase_is_asked_at_most_a_hundred_at_a_time(client, monkeypatch):
    sizes = []

    def get_users(identifiers):
        sizes.append(len(identifiers))

        return SimpleNamespace(users=[])

    async def preferences_of(session, user_ids):
        return {}

    monkeypatch.setattr(firebase_auth, "get_users", get_users)
    monkeypatch.setattr(emails, "preferences_of", preferences_of)

    client.post(
        "/internal/users/email-recipients",
        json={"user_ids": [f"u{index}" for index in range(250)]},
        headers=HEADERS,
    )

    assert sizes == [100, 100, 50]


def test_every_account_is_listed_a_page_at_a_time_for_a_notice_to_everyone(client, monkeypatch):
    everyone = [account(uid, f"{uid}@x.io") for uid in ["ann", "bob", "cy"]]
    asked = []

    def list_users(page_token=None):
        asked.append(page_token)
        later = [found for found in everyone if page_token is None or found.uid > page_token]

        return SimpleNamespace(iterate_all=lambda: iter(later))

    monkeypatch.setattr(firebase_auth, "list_users", list_users)

    first = client.get("/internal/users/ids", params={"limit": 2}, headers=HEADERS)
    rest = client.get("/internal/users/ids", params={"after": "bob", "limit": 2}, headers=HEADERS)

    assert first.json() == {"user_ids": ["ann", "bob"]}
    assert rest.json() == {"user_ids": ["cy"]}
    # Firebase goes on after the last id of the page before.
    assert asked == [None, "bob"]
    assert client.get("/internal/users/ids").status_code in (401, 403)


def test_a_campaign_asks_only_for_the_users_with_its_setting_on(client, monkeypatch):
    asked = []

    async def ids_with(session, setting, after, limit):
        asked.append((setting, after, limit))

        return ["ann"]

    monkeypatch.setattr(emails, "ids_with", ids_with)

    response = client.get("/internal/users/ids", params={"setting": "promotions"}, headers=HEADERS)
    later = client.get(
        "/internal/users/ids", params={"setting": "promotions", "after": "ann"}, headers=HEADERS
    )

    assert response.json() == later.json() == {"user_ids": ["ann"]}
    # A page at a time, after the last id of the one before.
    assert asked == [("promotions", "", 5000), ("promotions", "ann", 5000)]
    # Only the marketing settings, which are off until the user turns them on.
    assert client.get("/internal/users/ids?setting=reminders", headers=HEADERS).status_code == 422


def test_of_some_users_notifications_learns_who_has_a_campaigns_setting_on(client, monkeypatch):
    asked = []

    async def having(session, setting, user_ids):
        asked.append((setting, user_ids))

        return user_ids[:1]

    monkeypatch.setattr(emails, "having", having)
    body = {"user_ids": ["ann", "bob"], "setting": "promotions"}

    response = client.post("/internal/users/with-setting", json=body, headers=HEADERS)

    assert response.json() == {"user_ids": ["ann"]}
    assert asked == [("promotions", ["ann", "bob"])]
    # Only a campaign's settings, and only for a service.
    wrong = {**body, "setting": "reminders"}
    assert (
        client.post("/internal/users/with-setting", json=wrong, headers=HEADERS).status_code == 422
    )
    assert client.post("/internal/users/with-setting", json=body).status_code in (401, 403)
