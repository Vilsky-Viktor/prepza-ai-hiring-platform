from event_pushes import push
from prepza_common.auth.service_auth import issue_token

from notifications.models.slack import SlackConnection
from notifications.repositories import (
    bulk_recipients,
    note_notices,
    notifications,
    pending_notes,
    sent_emails,
    slack,
)

HEADERS = {
    "Authorization": f"Bearer {issue_token('library', 'notifications', 'test-secret-that-is-at-least-32-bytes')}"
}


def test_a_deleted_account_takes_their_notifications_and_sent_log_and_forgets_their_channels(
    client, monkeypatch
):
    done = []

    async def remove_user(session, user_id):
        done.append(("own", user_id))

    async def remove_candidate(session, email):
        done.append(("candidate", email))

    async def remove_member(session, email):
        done.append(("member", email))

    async def forget_maker(session, user_id):
        done.append(("slack", user_id))

        return []

    monkeypatch.setattr(notifications, "remove_user", remove_user)
    monkeypatch.setattr(notifications, "remove_candidate", remove_candidate)
    monkeypatch.setattr(notifications, "remove_member", remove_member)

    async def forget_sent(session, user_id):
        done.append(("sent", user_id))

    monkeypatch.setattr(slack, "forget_maker", forget_maker)

    async def forget_bulk(session, user_id):
        done.append(("bulk", user_id))

    monkeypatch.setattr(sent_emails, "remove_user", forget_sent)
    monkeypatch.setattr(bulk_recipients, "remove_user", forget_bulk)

    async def by_author(session, user_id):
        done.append(("note items", user_id))

        return []

    async def forget_author(session, user_id):
        done.append(("pending notes", user_id))

    monkeypatch.setattr(note_notices, "by_author", by_author)
    monkeypatch.setattr(pending_notes, "forget_author", forget_author)

    response = client.post(
        "/internal/events",
        json=push("user.deleted", {"user_id": "u1", "email": "ann@example.com"}),
    )

    assert response.status_code == 204
    assert done == [
        ("own", "u1"),
        ("note items", "u1"),
        ("pending notes", "u1"),
        ("sent", "u1"),
        ("bulk", "u1"),
        ("candidate", "ann@example.com"),
        ("member", "ann@example.com"),
        ("slack", "u1"),
    ]


def test_an_export_holds_the_slack_channels_they_connected(client, monkeypatch):
    async def latest(session, recipients, limit):
        return []

    async def made_by(session, user_id):
        return [SlackConnection(company_id="c1", team="Acme", channel="#hiring", created_at=None)]

    async def nothing(session, user_id):
        return []

    async def never_opened(session, user_id):
        return None

    monkeypatch.setattr(notifications, "latest", latest)
    monkeypatch.setattr(notifications, "seen_at", never_opened)
    monkeypatch.setattr(slack, "made_by", made_by)
    monkeypatch.setattr(sent_emails, "of_user", nothing)
    monkeypatch.setattr(bulk_recipients, "of_user", nothing)

    response = client.post("/internal/users/u1/export", headers=HEADERS)

    assert response.json() == {
        "notifications": [],
        "slack_channels": [{"company_id": "c1", "team": "Acme", "channel": "#hiring", "at": None}],
        "notifications_last_opened": None,
        "emails_sent": [],
        "emails_to_many": [],
    }
