import asyncio
import uuid

import pytest

from notifications.config import settings
from notifications.helpers.emails import contact_email
from notifications.helpers.unsubscribe import address_hash
from notifications.integrations import companies
from notifications.models.email import Email
from notifications.repositories import bulk_recipients, soft_bounces, suppressed
from notifications.services import delivery, suppression

CONTACT = {"name": "Eve", "email": "eve@example.com", "message": "Hi", "language": "en"}


@pytest.fixture
def suppressing(monkeypatch):
    state = {"added": [], "complained": [], "soft": {}}

    async def add(session, address, reason):
        state["added"].append((address, reason))

    async def mark_complained(session, send_id, user_id):
        state["complained"].append((str(send_id), user_id))

    async def add_soft(session, address, email_id, since):
        state["soft"].setdefault(address, set()).add(email_id)

        return len(state["soft"][address])

    monkeypatch.setattr(suppressed, "add", add)
    monkeypatch.setattr(bulk_recipients, "mark_complained", mark_complained)
    monkeypatch.setattr(soft_bounces, "add", add_soft)

    return state


def test_a_bounce_or_complaint_suppresses_a_members_address(suppressing):
    send = str(uuid.uuid4())
    complaint = {
        "type": "email.complained",
        "data": {"to": ["Ann@Example.com"], "tags": {"kind": "updates", "id": "ann", "send": send}},
    }
    bounce = {"type": "email.bounced", "data": {"to": ["bob@example.com"], "tags": {}}}
    resends = {"type": "email.suppressed", "data": {"to": ["cy@example.com"], "tags": {}}}

    asyncio.run(suppression.from_webhook(complaint))
    asyncio.run(suppression.from_webhook(bounce))
    asyncio.run(suppression.from_webhook(resends))

    assert suppressing["added"] == [
        (address_hash("ann@example.com"), "complained"),
        (address_hash("bob@example.com"), "bounced"),
        (address_hash("cy@example.com"), "suppressed"),
    ]
    assert suppressing["complained"] == [(send, "ann")]


def test_a_candidates_bounce_suppresses_and_another_event_nothing(suppressing):
    invite = {
        "type": "email.bounced",
        "data": {"to": ["cat@example.com"], "tags": {"kind": "candidate_invite", "id": "i"}},
    }
    delivered = {"type": "email.delivered", "data": {"to": ["cy@example.com"]}}

    asyncio.run(suppression.from_webhook(invite))
    asyncio.run(suppression.from_webhook(delivered))

    assert suppressing["added"] == [(address_hash("cat@example.com"), "bounced")]


@pytest.fixture
def outbox(monkeypatch):
    """What delivery hands to Resend, the invites reported undelivered, and the addresses on
    the list."""
    state = {"sent": [], "undelivered": [], "listed": set()}

    async def transmit(email, key):
        state["sent"].append(email.to)

    async def get(session, address):
        return object() if address in state["listed"] else None

    async def undelivered(invite_id):
        state["undelivered"].append(invite_id)

    monkeypatch.setattr(delivery, "transmit", transmit)
    monkeypatch.setattr(suppressed, "get", get)
    monkeypatch.setattr(companies, "invite_undelivered", undelivered)

    return state


def test_nothing_goes_to_a_suppressed_address_and_an_invite_shows_undelivered(outbox):
    outbox["listed"] = {address_hash("cat@example.com"), address_hash(settings.contact_email)}
    invite = Email(to="Cat@example.com", subject="s", html="h", text="t")
    invite.tags = {"kind": "candidate_invite", "id": "i-1"}

    asyncio.run(delivery.send(invite, "k1"))
    asyncio.run(delivery.send(Email(to="dan@example.com", subject="s", html="h", text="t"), "k2"))
    # The contact page's messages reach prepza's own inbox whatever the list says.
    asyncio.run(delivery.send(contact_email(CONTACT, settings.contact_email), "k3"))

    assert outbox["sent"] == ["dan@example.com", settings.contact_email]
    assert outbox["undelivered"] == ["i-1"]


def bounce(kind, email_id="e-1", to="dan@example.com"):
    return {
        "type": "email.bounced",
        "data": {"to": [to], "email_id": email_id, "bounce": {"type": kind}, "tags": {}},
    }


def test_a_permanent_bounce_suppresses_at_once_a_temporary_one_only_counts(suppressing):
    asyncio.run(suppression.from_webhook(bounce("Permanent", to="eve@example.com")))
    asyncio.run(suppression.from_webhook(bounce("Temporary")))

    assert suppressing["added"] == [(address_hash("eve@example.com"), "bounced")]
    assert suppressing["soft"] == {address_hash("dan@example.com"): {"e-1"}}


def test_repeated_soft_bounces_suppress_and_a_repeated_web_hook_counts_once(suppressing):
    for email_id in ("e-1", "e-1", "e-2"):
        asyncio.run(suppression.from_webhook(bounce("Temporary", email_id)))

    assert suppressing["added"] == []

    asyncio.run(suppression.from_webhook(bounce("Temporary", "e-3")))

    assert suppressing["added"] == [(address_hash("dan@example.com"), "soft_bounced")]
