import base64
import json
import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.events.notifications import (
    NOTIFICATION_REQUESTED,
    NotificationKind,
    notification,
)

from app.main import app
from app.models.notifications import Notification
from app.services import events, feed
from app.storage import notifications

MADE = datetime(2026, 10, 1, tzinfo=UTC)
EVENT = notification(
    "company", "c1", NotificationKind.CANDIDATE_FINISHED, "/companies/c1", email="a@b.c"
)


def push(message_id):
    return {
        "message": {
            "data": base64.b64encode(json.dumps(EVENT).encode()).decode(),
            "attributes": {"type": NOTIFICATION_REQUESTED},
            "messageId": message_id,
        },
        "subscription": "projects/demo-test/subscriptions/notifications-events",
    }


@pytest.fixture(autouse=True)
def emulator(monkeypatch):
    monkeypatch.setenv("PUBSUB_EMULATOR_HOST", "pubsub:8085")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-test")
    yield
    app.dependency_overrides.clear()


def sign_in():
    app.dependency_overrides[current_user] = lambda: User(
        uid="u1", email="u1@example.com", email_verified=True, name="Ann"
    )


def test_a_notification_is_stored_and_announced_once(client, monkeypatch):
    stored, announced = set(), []

    async def fake_add(event_id, data):
        new = event_id not in stored
        stored.add(event_id)

        return new

    async def fake_announce(recipient, recipient_id):
        announced.append((recipient, recipient_id))

    monkeypatch.setattr(notifications, "add", fake_add)
    monkeypatch.setattr(events, "announce", fake_announce)

    assert client.post("/internal/events", json=push("m-1")).status_code == 204
    # Pub/Sub delivering it again: stored once, announced once.
    assert client.post("/internal/events", json=push("m-1")).status_code == 204
    assert announced == [("company", "c1")]


def test_the_bell_shows_the_users_and_their_companies_notifications(client, monkeypatch):
    sign_in()
    asked = {}

    async def fake_companies(user_id):
        return ["c1"]

    async def fake_latest(recipients, limit, since):
        asked["recipients"], asked["limit"], asked["since"] = recipients, limit, since

        return [
            Notification(
                id=uuid.uuid4(),
                kind="candidate_finished",
                link="/companies/c1",
                data={"email": "a@b.c"},
                created_at=datetime.now(UTC),
            )
        ]

    async def fake_unread(recipients, user_id, since):
        return 3

    async def fake_created(user_id):
        return MADE

    monkeypatch.setattr(feed.companies, "company_ids", fake_companies)
    monkeypatch.setattr(notifications, "latest", fake_latest)
    monkeypatch.setattr(notifications, "unread_count", fake_unread)
    monkeypatch.setattr(feed.library, "account_created", fake_created)

    body = client.get("/me").json()

    # Everyone's notifications too, newer than the account.
    assert asked == {
        "recipients": [("user", "u1"), ("company", "c1")],
        "limit": 10,
        "since": MADE,
    }
    assert body["unread"] == 3
    assert body["items"][0]["kind"] == "candidate_finished"
    assert body["items"][0]["data"] == {"email": "a@b.c"}


def test_opening_the_bell_marks_everything_seen(client, monkeypatch):
    sign_in()
    seen = []

    async def fake_mark(user_id):
        seen.append(user_id)

    monkeypatch.setattr(notifications, "mark_seen", fake_mark)

    assert client.post("/me/seen").status_code == 204
    assert seen == ["u1"]


def test_only_services_delete_or_export_a_users_notifications(client):
    assert client.delete("/internal/users/u1").status_code in (401, 403)
    assert client.post("/internal/users/u1/export").status_code in (401, 403)
