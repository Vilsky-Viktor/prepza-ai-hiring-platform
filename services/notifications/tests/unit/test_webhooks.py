import base64
import hashlib
import hmac
import json
import time

import pytest
from prepza_common.constants import WEBHOOK_SIGNATURE_REFUSED

from app.config.settings import settings
from app.helpers.emails import candidate_invite_email
from app.helpers.webhooks import signature_valid
from app.integrations import companies, library
from app.storage import suppressed

# Svix's published example (docs.svix.com, "Verifying Webhooks Manually"), not a real secret. Put
# together from parts so secret scanners don't take the literal for a leaked key.
SVIX_SECRET = "whsec_" + "plJ3nmyCDGBKInavdOK15jsl"
SVIX_BODY = b'{"event_type":"ping","data":{"success":true}}'
SVIX_ID = "msg_loFOjxBNrRLzqYUf"
SVIX_TIMESTAMP = "1731705121"
SVIX_SIGNATURE = "v1,rAvfW3dJ/X/qxhsaXPOyyCGmRKsaKWcsNccKXlIktD0="

SECRET = "whsec_" + base64.b64encode(b"test-webhook-key").decode()
INVITE_ID = "6f1c2c1e-0000-4000-8000-000000000001"


def valid(signature=SVIX_SIGNATURE, now=int(SVIX_TIMESTAMP), secret=SVIX_SECRET):
    return signature_valid(SVIX_ID, SVIX_TIMESTAMP, signature, SVIX_BODY, secret, now, 300)


def test_svix_example_signature_is_accepted():
    assert valid()


def test_signature_list_with_other_versions_is_accepted():
    assert valid(f"v2,abc {SVIX_SIGNATURE}")


def test_wrong_signature_stale_timestamp_or_no_secret_is_refused():
    assert not valid("v1,rAvfW3dJ/X/qxhsaXPOyyCGmRKsaKWcsNccKXlIktD0x")
    assert not valid(now=int(SVIX_TIMESTAMP) + 301)
    assert not valid(secret="")


def signed_post(client, event: dict):
    """Posts the event as Resend would, signed with SECRET."""
    body = json.dumps(event).encode()
    timestamp = str(int(time.time()))
    key = base64.b64decode(SECRET.removeprefix("whsec_"))
    digest = hmac.new(key, f"msg_1.{timestamp}.".encode() + body, hashlib.sha256).digest()
    headers = {
        "svix-id": "msg_1",
        "svix-timestamp": timestamp,
        "svix-signature": "v1," + base64.b64encode(digest).decode(),
        "content-type": "application/json",
    }

    return client.post("/webhooks/resend", content=body, headers=headers)


@pytest.fixture
def reported(monkeypatch):
    """Records which owner was told about which invite."""
    calls = []

    async def fake_invite(invite_id):
        calls.append(("companies", invite_id))

    async def fake_unsubscribe(user_id, email_settings):
        calls.append(("library", user_id, email_settings))

    monkeypatch.setattr(settings, "resend_webhook_secret", SECRET)
    monkeypatch.setattr(companies, "invite_undelivered", fake_invite)

    # The suppression list has its own tests (test_bell_for_everyone.py).
    async def fake_suppress(address, reason):
        return None

    monkeypatch.setattr(library, "unsubscribe", fake_unsubscribe)
    monkeypatch.setattr(suppressed, "add", fake_suppress)

    return calls


def event(event_type, kind=None, tag_id=INVITE_ID):
    tags = {"kind": kind, "id": tag_id} if kind else {}

    return {"type": event_type, "data": {"to": ["bob@example.com"], "tags": tags}}


def test_a_bounced_candidate_invite_is_reported_to_companies(client, reported):
    assert signed_post(client, event("email.bounced", "candidate_invite")).status_code == 204
    assert reported == [("companies", INVITE_ID)]


def test_a_spam_complaint_on_an_invite_is_reported_to_companies(client, reported):
    assert signed_post(client, event("email.complained", "candidate_invite")).status_code == 204
    assert reported == [("companies", INVITE_ID)]


def test_an_invite_resend_failed_to_send_is_reported_to_companies(client, reported):
    assert signed_post(client, event("email.failed", "candidate_invite")).status_code == 204
    assert reported == [("companies", INVITE_ID)]


def test_other_events_and_untagged_emails_are_ignored(client, reported):
    assert signed_post(client, event("email.delivered", "candidate_invite")).status_code == 204
    assert signed_post(client, event("email.bounced")).status_code == 204
    assert reported == []


def test_an_unsigned_webhook_is_refused(client, reported, caplog):
    response = client.post("/webhooks/resend", json=event("email.bounced", "candidate_invite"))

    assert response.status_code == 401
    assert reported == []
    # Logged as an error, which the alert for a wrong web hook secret matches.
    assert [r.levelname for r in caplog.records if WEBHOOK_SIGNATURE_REFUSED in r.message] == [
        "ERROR"
    ]


def test_invite_emails_are_tagged_with_what_they_are():
    base = {"email": "bob@example.com", "token": "t", "title": "Backend"}
    invite = candidate_invite_email(
        {**base, "company": "Acme", "invite_id": INVITE_ID}, "http://x", "secret"
    )
    untagged = candidate_invite_email({**base, "company": "Acme"}, "http://x", "secret")

    assert invite.tags == {"kind": "candidate_invite", "id": INVITE_ID}
    assert untagged.tags == {}


def test_a_spam_complaint_on_the_digest_turns_the_users_digest_off(client, reported):
    assert signed_post(client, event("email.complained", "digest", "ann")).status_code == 204
    assert reported == [
        (
            "library",
            "ann",
            ["candidate_finished", "invite_undelivered", "ats_not_invited", "interview_ready"],
        )
    ]


def test_a_spam_complaint_on_a_reminder_turns_reminders_off(client, reported):
    signed_post(client, event("email.complained", "reminders", "ann"))

    assert reported == [("library", "ann", ["reminders"])]


def test_a_bounce_on_an_optional_email_changes_no_settings(client, reported):
    signed_post(client, event("email.bounced", "digest", "ann"))
    signed_post(client, event("email.suppressed", "reminders", "ann"))

    assert reported == []


def test_a_signature_beyond_ascii_is_refused_not_an_error():
    secret = "whsec_" + base64.b64encode(b"key").decode()

    assert signature_valid("m1", "1000", "v1,ä", b"{}", secret, 1000, 300) is False
